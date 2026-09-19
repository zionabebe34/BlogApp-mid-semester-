"""
BlogApp backend (Flask + MySQL).

How a request flows through this file:

1. The browser sends a request, carrying a `session_id` cookie if the user
   is logged in (the cookie is set by /api/login).
2. Routes that require a logged-in user call `current_user_id()`, which
   translates the session cookie into a user id via the `sessions` table.
3. Each request borrows a MySQL connection from a shared pool (`get_db`)
   and returns it automatically when the request ends (`close_db`).

Route groups (in order below):
   - Auth:      /api/signup                    (create account)
                /api/login                     (log in, sets session cookie)
                /api/logout                    (log out, clears session)
                /api/me                        (who is logged in)
   - Profile:   /api/me/bio                    (update my bio)
                /api/users/<id>/profile        (full profile + posts)
   - Posts:     /api/feed                      (global feed, paginated)
                /api/feed/following            (feed from followed users)
                /api/new-post                  (create a post)
                /api/user-posts/<id>           (posts by one user)
   - Users:     /api/users                     (list users + post counts)
                /api/users/search              (search by name/email)
   - Social:    /api/users/<id>/follow         (follow a user)
                /api/users/<id>/unfollow       (unfollow a user)
                /api/users/<id>/followers      (who follows this user)
                /api/users/<id>/following      (who this user follows)
                /api/posts/<id>/like           (like a post)
                /api/posts/<id>/unlike         (remove a like)
                /api/posts/<id>/likes          (like count + did I like it)
                /api/user-posts/<id>/comments  (GET: list comments, POST: add one)
                /api/posts/<id>/report         (flag a post for review)
   - Admin:     /api/admin/reports             (open reports; admin/moderator)
                /api/admin/reports/<id>        (resolve or dismiss a report)
                /api/admin/posts/<id>          (DELETE offending content)
                /api/admin/users/<id>/ban      (ban a user; admin only)
                /api/admin/users/<id>/unban    (lift a ban; admin only)
   - Reset:     /api/forgot-password           (email a one-time reset link)
                /api/reset-password            (consume the token, set password)
"""

import hashlib
import os
import secrets
import smtplib
import uuid
from datetime import datetime, timedelta
from email.message import EmailMessage
from functools import wraps

import bcrypt
import mysql.connector
from mysql.connector import pooling
from dotenv import load_dotenv
from flask import Flask, request, jsonify, make_response, g
from flask_cors import CORS

# Load DB_HOST / DB_USER / DB_PASSWORD / DB_NAME from config.env
load_dotenv('config.env')

app = Flask(__name__)
CORS(
    app,
    origins=['http://localhost:5173', 'http://127.0.0.1:5173', 'http://localhost:3000'],
    supports_credentials=True,  # allow the session cookie to travel with requests
)

# MySQL duplicate/constraint error codes we handle explicitly
ERR_DUPLICATE_ENTRY = 1062
ERR_FOREIGN_KEY = 1452

# How long a password-reset link stays valid
RESET_TOKEN_TTL_HOURS = 1


# ── Database connection ──────────────────────────────────────────────────────
# A single shared connection is NOT safe across Flask's worker threads:
# concurrent requests using the same MySQL connection crash the C driver
# (double-free in SSL_free). Instead we use a pool and hand each request
# its own connection, returning it when the request ends.
connection_pool = pooling.MySQLConnectionPool(
    pool_name='blogapp_pool',
    pool_size=10,
    pool_reset_session=True,
    host=os.getenv('DB_HOST'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME'),
    use_pure=True,  # pure-Python driver: avoids the native SSL_free crash
)


def get_db():
    """Return this request's connection, borrowing one from the pool once."""
    if 'db' not in g:
        g.db = connection_pool.get_connection()
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    """Return the connection to the pool when the request finishes."""
    db = g.pop('db', None)
    if db is not None:
        db.close()


# ── Auth helper ──────────────────────────────────────────────────────────────
def current_user_id():
    """
    Return the id of the logged-in user, or None if nobody is logged in.

    The browser sends a `session_id` cookie; we look it up in the
    `sessions` table to find which user it belongs to.
    """
    session_id = request.cookies.get('session_id')
    if not session_id:
        return None

    # Banned users are excluded here too, so an existing session stops working
    # the moment the ban lands — not just on their next login attempt.
    cursor = get_db().cursor()
    cursor.execute(
        """
        SELECT sessions.user_id
        FROM sessions
        JOIN users ON sessions.user_id = users.id
        WHERE sessions.session_id = %s AND users.is_banned = FALSE
        """,
        (session_id,),
    )
    row = cursor.fetchone()
    cursor.close()
    return row[0] if row else None


def current_user_role():
    """
    Return the role of the logged-in user ('user' / 'moderator' / 'admin'),
    or None if nobody is logged in.
    """
    session_id = request.cookies.get('session_id')
    if not session_id:
        return None

    cursor = get_db().cursor()
    cursor.execute(
        """
        SELECT users.role
        FROM sessions
        JOIN users ON sessions.user_id = users.id
        WHERE sessions.session_id = %s
        """,
        (session_id,),
    )
    row = cursor.fetchone()
    cursor.close()
    return row[0] if row else None


def roles_required(*allowed_roles):
    """
    Route decorator: reject anyone whose role is not in `allowed_roles`.

        @app.route('/api/admin/reports')
        @roles_required('admin', 'moderator')
        def list_reports():
            ...

    401 means "I don't know who you are"; 403 means "I know exactly who you
    are, and you're not allowed in".
    """
    def decorator(view_function):
        @wraps(view_function)
        def wrapper(*args, **kwargs):
            role = current_user_role()
            if role is None:
                return jsonify({'message': 'Unauthorized'}), 401
            if role not in allowed_roles:
                return jsonify({'message': 'Forbidden - insufficient permissions'}), 403
            return view_function(*args, **kwargs)
        return wrapper
    return decorator


# ── Password reset helpers ───────────────────────────────────────────────────
def hash_reset_token(token):
    """
    Hash a reset token before storing it, for the same reason we hash
    passwords: a leaked table should not hand out working tokens.

    SHA-256 (not bcrypt) is enough here — the token is 32 random bytes,
    so there is nothing to brute-force.
    """
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


def send_reset_email(email, token):
    """
    Email the reset link over SMTP.

    Everything environment-specific lives in config.env, so moving to AWS SES
    at deployment is a config change, not a code change. If SMTP isn't
    configured (tests, fresh clone) we fall back to printing the link.
    """
    base_url = os.getenv('APP_BASE_URL', 'http://localhost:5174')
    reset_url = f"{base_url}/reset-password?token={token}"

    host = os.getenv('SMTP_HOST')
    user = os.getenv('SMTP_USER')
    password = os.getenv('SMTP_PASSWORD')

    if not (host and user and password):
        print(f"\n[password reset] for {email}: {reset_url}\n", flush=True)
        return

    message = EmailMessage()
    message['Subject'] = 'Reset your HandyHub password'
    message['From'] = user
    message['To'] = email
    message.set_content(
        "Someone asked to reset the password for this HandyHub account.\n\n"
        f"Open this link within {RESET_TOKEN_TTL_HOURS} hour(s) to choose a new password:\n"
        f"{reset_url}\n\n"
        "If this wasn't you, you can ignore this email — nothing has changed."
    )

    try:
        with smtplib.SMTP(host, int(os.getenv('SMTP_PORT', 587))) as smtp:
            smtp.starttls()  # encrypt the connection before sending credentials
            smtp.login(user, password)
            smtp.send_message(message)
    except Exception as err:
        # A mail failure must not reveal whether the address exists
        print(f"[password reset] failed to email {email}: {err}", flush=True)


def serialize_timestamps(posts):
    """Convert each post's `created_at` datetime to an ISO string for JSON."""
    for post in posts:
        if post['created_at']:
            post['created_at'] = post['created_at'].isoformat()
    return posts


# ═════════════════════════════════════════════════════════════════════════════
# Auth routes
# ═════════════════════════════════════════════════════════════════════════════

@app.route('/api/signup', methods=['POST'])
def signup():
    """Create a new user with a hashed password, default bio and avatar."""
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password_plain = data.get('password')

    if not name or not email or not password_plain:
        return jsonify({"error": "Missing required fields"}), 400

    # A unique avatar generated from the email (emails are unique in the DB)
    avatar_url = f"https://api.dicebear.com/7.x/avataaars/svg?seed={email}"
    default_bio = "Hello, I am new to BlogApp!"

    # Never store the plain password — only the bcrypt hash
    hashed_password = bcrypt.hashpw(password_plain.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    try:
        cursor = get_db().cursor()
        cursor.execute(
            """
            INSERT INTO users (name, email, password, bio, profile_picture_url)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (name, email, hashed_password, default_bio, avatar_url),
        )
        get_db().commit()
        cursor.close()
        return jsonify({"message": "User registered successfully!"}), 201

    except mysql.connector.Error as err:
        if err.errno == ERR_DUPLICATE_ENTRY:
            return jsonify({"error": "Email already exists"}), 400
        return jsonify({"error": "Database error occurred"}), 500


@app.route('/api/login', methods=['POST'])
def login():
    """Verify credentials, create a session row, and set the session cookie."""
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    # Listing the columns explicitly (instead of SELECT *) keeps this code
    # independent of the order columns happen to have in the table.
    cursor = get_db().cursor()
    cursor.execute(
        "SELECT id, name, password, is_banned FROM users WHERE email = %s",
        (email,),
    )
    user = cursor.fetchone()

    if not user:
        return jsonify({'message': 'Invalid email or password'}), 401

    user_id, name, hashed_password, is_banned = user

    if not bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8')):
        return jsonify({'message': 'Invalid email or password'}), 401

    if is_banned:
        return jsonify({'message': 'This account has been banned'}), 403

    # Create a fresh session id (replacing any previous one for this user)
    session_id = str(uuid.uuid4())
    cursor.execute(
        "INSERT INTO sessions (user_id, session_id) VALUES (%s, %s) "
        "ON DUPLICATE KEY UPDATE session_id = %s",
        (user_id, session_id, session_id),
    )
    get_db().commit()

    # The cookie is how the browser proves who it is on future requests
    response = make_response(jsonify({'message': 'Login successful', 'email': email, 'name': name}))
    response.set_cookie('session_id', session_id, httponly=True, samesite='Lax')
    return response, 200


@app.route('/api/logout', methods=['POST'])
def logout():
    """Delete the session row and clear the cookie."""
    session_id = request.cookies.get('session_id')
    if session_id:
        cursor = get_db().cursor()
        cursor.execute("DELETE FROM sessions WHERE session_id = %s", (session_id,))
        get_db().commit()

    response = make_response(jsonify({'message': 'Logout successful'}))
    response.delete_cookie('session_id')
    return response, 200


@app.route('/api/forgot-password', methods=['POST'])
def forgot_password():
    """
    Start a reset. Always answers 200, even for an unknown address — telling
    a stranger whether an email is registered leaks who your users are
    (user enumeration).
    """
    email = request.get_json().get('email', '').strip()
    generic_reply = jsonify({'message': 'If that email exists, a reset link has been sent'}), 200

    if not email:
        return generic_reply

    cursor = get_db().cursor()
    cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
    row = cursor.fetchone()

    if row:
        user_id = row[0]
        token = secrets.token_urlsafe(32)  # `secrets`, not `random`: unpredictable
        expires_at = datetime.now() + timedelta(hours=RESET_TOKEN_TTL_HOURS)

        cursor.execute(
            "INSERT INTO password_resets (user_id, token_hash, expires_at) VALUES (%s, %s, %s)",
            (user_id, hash_reset_token(token), expires_at),
        )
        get_db().commit()
        send_reset_email(email, token)

    cursor.close()
    return generic_reply


@app.route('/api/reset-password', methods=['POST'])
def reset_password():
    """Finish a reset: verify the token, set the new password, burn the token."""
    data = request.get_json()
    token = data.get('token', '').strip()
    new_password = data.get('password', '')

    if not token or not new_password:
        return jsonify({'message': 'Token and password are required'}), 400
    if len(new_password) < 6:
        return jsonify({'message': 'Password must be at least 6 characters'}), 400

    # All three conditions in one query: right token, unused, not expired
    cursor = get_db().cursor()
    cursor.execute(
        """
        SELECT id, user_id FROM password_resets
        WHERE token_hash = %s AND used_at IS NULL AND expires_at > NOW()
        """,
        (hash_reset_token(token),),
    )
    row = cursor.fetchone()

    if not row:
        cursor.close()
        return jsonify({'message': 'This reset link is invalid or has expired'}), 400

    reset_id, user_id = row
    hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    cursor.execute("UPDATE users SET password = %s WHERE id = %s", (hashed, user_id))
    cursor.execute("UPDATE password_resets SET used_at = NOW() WHERE id = %s", (reset_id,))
    # Anyone signed in with the old password is logged out
    cursor.execute("DELETE FROM sessions WHERE user_id = %s", (user_id,))
    get_db().commit()
    cursor.close()

    return jsonify({'message': 'Password updated successfully'}), 200


@app.route('/api/me', methods=['GET'])
def me():
    """Tell the frontend who is currently logged in (id, name, email)."""
    session_id = request.cookies.get('session_id')
    if not session_id:
        return jsonify({'message': 'Not logged in'}), 401

    cursor = get_db().cursor()
    cursor.execute(
        """
        SELECT users.id, users.name, users.email, users.role
        FROM sessions
        JOIN users ON sessions.user_id = users.id
        WHERE sessions.session_id = %s
        """,
        (session_id,),
    )
    user = cursor.fetchone()

    if not user:
        return jsonify({'message': 'Invalid session'}), 401

    return jsonify({'id': user[0], 'name': user[1], 'email': user[2], 'role': user[3]}), 200


# ═════════════════════════════════════════════════════════════════════════════
# Profile routes
# ═════════════════════════════════════════════════════════════════════════════

@app.route('/api/me/bio', methods=['PUT'])
def update_my_bio():
    """Let the logged-in user edit their own bio."""
    user_id = current_user_id()
    if user_id is None:
        return jsonify({'message': 'Unauthorized'}), 401

    new_bio = request.get_json().get('bio', '')

    cursor = get_db().cursor()
    cursor.execute("UPDATE users SET bio = %s WHERE id = %s", (new_bio, user_id))
    get_db().commit()
    cursor.close()

    return jsonify({'message': 'Bio updated successfully', 'bio': new_bio}), 200


@app.route('/api/users/<int:user_id>/profile', methods=['GET'])
def get_user_profile(user_id):
    """
    Everything the profile page needs in one response:
    user details + follower/following counts + "am I following them?" + posts.
    """
    viewer_id = current_user_id()  # may be None for anonymous visitors

    cursor = get_db().cursor(dictionary=True)

    cursor.execute(
        "SELECT id, name, email, bio, profile_picture_url FROM users WHERE id = %s",
        (user_id,),
    )
    user = cursor.fetchone()
    if not user:
        cursor.close()
        return jsonify({'message': 'User not found'}), 404

    cursor.execute("SELECT COUNT(*) as count FROM follows WHERE followed_id = %s", (user_id,))
    followers = cursor.fetchone()['count']

    cursor.execute("SELECT COUNT(*) as count FROM follows WHERE follower_id = %s", (user_id,))
    following = cursor.fetchone()['count']

    # Does the logged-in viewer already follow this profile?
    is_following = False
    if viewer_id is not None:
        cursor.execute(
            "SELECT 1 FROM follows WHERE follower_id = %s AND followed_id = %s",
            (viewer_id, user_id),
        )
        is_following = cursor.fetchone() is not None

    cursor.execute(
        "SELECT id, title, body, image_url, created_at FROM posts "
        "WHERE author_id = %s ORDER BY created_at DESC",
        (user_id,),
    )
    posts = serialize_timestamps(cursor.fetchall())
    cursor.close()

    return jsonify({
        **user,
        'followers_count': followers,
        'following_count': following,
        'is_following': is_following,
        'posts': posts,
    }), 200


# ═════════════════════════════════════════════════════════════════════════════
# Post / feed routes
# ═════════════════════════════════════════════════════════════════════════════

@app.route('/api/feed', methods=['GET'])
def feed():
    """Global feed: newest posts first, paginated with limit/offset."""
    limit = int(request.args.get('limit', 10))
    offset = int(request.args.get('offset', 0))

    cursor = get_db().cursor(dictionary=True)
    cursor.execute(
        """
        SELECT posts.id, posts.title, posts.body, posts.image_url, posts.created_at,
               users.name as author_name, users.email as author_email, users.profile_picture_url
        FROM posts
        JOIN users ON posts.author_id = users.id
        ORDER BY posts.created_at DESC
        LIMIT %s OFFSET %s
        """,
        (limit, offset),
    )
    results = serialize_timestamps(cursor.fetchall())
    cursor.close()
    return jsonify(results), 200


@app.route('/api/feed/following', methods=['GET'])
def feed_following():
    """Personal feed: posts only from users the logged-in user follows."""
    user_id = current_user_id()
    if user_id is None:
        return jsonify({'message': 'Unauthorized'}), 401

    cursor = get_db().cursor(dictionary=True)
    cursor.execute(
        """
        SELECT posts.id, posts.title, posts.body, posts.image_url, posts.created_at,
               users.name as author_name, users.email as author_email, users.profile_picture_url
        FROM posts
        JOIN follows ON posts.author_id = follows.followed_id
        JOIN users ON posts.author_id = users.id
        WHERE follows.follower_id = %s
        ORDER BY posts.created_at DESC
        """,
        (user_id,),
    )
    results = serialize_timestamps(cursor.fetchall())
    cursor.close()
    return jsonify(results), 200


@app.route('/api/new-post', methods=['POST'])
def new_post():
    """Create a post authored by the logged-in user (body is rich-text HTML)."""
    author_id = current_user_id()
    if author_id is None:
        return jsonify({'message': 'Unauthorized'}), 401

    data = request.get_json()
    title = data.get('title', '').strip()
    body = data.get('body', '')
    image_url = data.get('image_url')

    if not title or not body:
        return jsonify({'message': 'Title and body are required'}), 400

    cursor = get_db().cursor()
    cursor.execute(
        "INSERT INTO posts (title, body, image_url, author_id) VALUES (%s, %s, %s, %s)",
        (title, body, image_url, author_id),
    )
    get_db().commit()

    return jsonify({'message': 'Post created successfully'}), 201


@app.route('/api/user-posts/<int:user_id>', methods=['GET'])
def get_user_posts(user_id):
    """All posts written by one user (plus their name for the page title)."""
    cursor = get_db().cursor()
    cursor.execute("SELECT name FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    user_name = user[0] if user else f'User #{user_id}'

    cursor.execute("SELECT id, title, body FROM posts WHERE author_id = %s", (user_id,))
    posts = [{'id': row[0], 'title': row[1], 'body': row[2]} for row in cursor.fetchall()]
    return jsonify({'user_name': user_name, 'posts': posts}), 200


# ═════════════════════════════════════════════════════════════════════════════
# User list / search routes
# ═════════════════════════════════════════════════════════════════════════════

@app.route('/api/users', methods=['GET'])
def get_users():
    """All users with how many posts each has written."""
    cursor = get_db().cursor()
    cursor.execute(
        """
        SELECT users.id, users.name, users.email, COUNT(posts.id) as post_count
        FROM users
        LEFT JOIN posts ON posts.author_id = users.id
        GROUP BY users.id, users.name, users.email
        """
    )
    users = [
        {'id': row[0], 'name': row[1], 'email': row[2], 'postCount': row[3]}
        for row in cursor.fetchall()
    ]
    return jsonify(users), 200


@app.route('/api/users/search', methods=['GET'])
def search_users():
    """Partial-match search on name or email, e.g. /api/users/search?q=zion."""
    query = request.args.get('q', '')
    if not query:
        return jsonify([]), 200

    # % is the SQL wildcard, so %query% means "contains this string"
    search_pattern = f"%{query}%"

    cursor = get_db().cursor(dictionary=True)
    cursor.execute(
        """
        SELECT users.id, users.name, users.email, users.profile_picture_url,
               COUNT(posts.id) as postCount
        FROM users
        LEFT JOIN posts ON posts.author_id = users.id
        WHERE users.name LIKE %s OR users.email LIKE %s
        GROUP BY users.id, users.name, users.email, users.profile_picture_url
        """,
        (search_pattern, search_pattern),
    )
    results = cursor.fetchall()
    cursor.close()
    return jsonify(results), 200


# ═════════════════════════════════════════════════════════════════════════════
# Social routes (follow / unfollow)
# ═════════════════════════════════════════════════════════════════════════════

@app.route('/api/users/<int:user_id>/follow', methods=['POST'])
def follow_user(user_id):
    """Make the logged-in user follow `user_id`."""
    follower_id = current_user_id()
    if follower_id is None:
        return jsonify({'message': 'Unauthorized'}), 401

    if follower_id == user_id:
        return jsonify({'message': 'You cannot follow yourself'}), 400

    try:
        cursor = get_db().cursor()
        cursor.execute(
            "INSERT INTO follows (follower_id, followed_id) VALUES (%s, %s)",
            (follower_id, user_id),
        )
        get_db().commit()
        cursor.close()
        return jsonify({'message': 'Successfully followed user'}), 200

    except mysql.connector.Error as err:
        if err.errno == ERR_DUPLICATE_ENTRY:
            return jsonify({'message': 'You are already following this user'}), 400
        if err.errno == ERR_FOREIGN_KEY:
            return jsonify({'message': 'User to follow does not exist'}), 404
        return jsonify({'message': 'Database error occurred'}), 500


@app.route('/api/users/<int:user_id>/unfollow', methods=['POST'])
def unfollow_user(user_id):
    """Make the logged-in user unfollow `user_id`."""
    follower_id = current_user_id()
    if follower_id is None:
        return jsonify({'message': 'Unauthorized'}), 401

    try:
        cursor = get_db().cursor()
        cursor.execute(
            "DELETE FROM follows WHERE follower_id = %s AND followed_id = %s",
            (follower_id, user_id),
        )
        get_db().commit()
        cursor.close()
        return jsonify({'message': 'Successfully unfollowed user'}), 200

    except mysql.connector.Error:
        return jsonify({'message': 'Database error occurred'}), 500


@app.route('/api/users/<int:user_id>/followers', methods=['GET'])
def get_followers(user_id):
    """Everyone who follows this user."""
    cursor = get_db().cursor(dictionary=True)
    cursor.execute(
        """
        SELECT users.id, users.name, users.email, users.profile_picture_url
        FROM follows
        JOIN users ON follows.follower_id = users.id
        WHERE follows.followed_id = %s
        """,
        (user_id,),
    )
    results = cursor.fetchall()
    cursor.close()
    return jsonify(results), 200


@app.route('/api/users/<int:user_id>/following', methods=['GET'])
def get_following(user_id):
    """Everyone this user follows."""
    cursor = get_db().cursor(dictionary=True)
    cursor.execute(
        """
        SELECT users.id, users.name, users.email, users.profile_picture_url
        FROM follows
        JOIN users ON follows.followed_id = users.id
        WHERE follows.follower_id = %s
        """,
        (user_id,),
    )
    results = cursor.fetchall()
    cursor.close()
    return jsonify(results), 200


# ═════════════════════════════════════════════════════════════════════════════
# Social routes (like / unlike)
# ═════════════════════════════════════════════════════════════════════════════

@app.route('/api/posts/<int:post_id>/like', methods=['POST'])
def like_post(post_id):
    """Make the logged-in user like `post_id`."""
    user_id = current_user_id()
    if user_id is None:
        return jsonify({'message': 'Unauthorized'}), 401

    try:
        cursor = get_db().cursor()
        cursor.execute(
            "INSERT INTO likes (user_id, post_id) VALUES (%s, %s)",
            (user_id, post_id),
        )
        get_db().commit()
        cursor.close()
        return jsonify({'message': 'Post liked successfully'}), 200

    except mysql.connector.Error as err:
        if err.errno == ERR_DUPLICATE_ENTRY:
            return jsonify({'message': 'You already liked this post'}), 400
        if err.errno == ERR_FOREIGN_KEY:
            return jsonify({'message': 'Post does not exist'}), 404
        return jsonify({'message': 'Database error occurred'}), 500


@app.route('/api/posts/<int:post_id>/unlike', methods=['POST'])
def unlike_post(post_id):
    """Make the logged-in user unlike 'post_id'."""
    user_id = current_user_id()

    if user_id is None:
        return jsonify({'message': 'Unauthorized'}), 401
    try:
        cursor = get_db().cursor()
        query = "DELETE FROM likes WHERE user_id = %s AND post_id = %s"
        cursor.execute(query, (user_id, post_id))
        get_db().commit()
        cursor.close()
        return jsonify({'message': 'Post unliked successfully'}), 200
    except mysql.connector.Error as err:
        cursor.close()
        return jsonify({'message': f'Database error: {err}'}), 500

@app.route('/api/posts/<int:post_id>/likes', methods=['GET'])
def get_post_likes(post_id):
        """Return the like count for a post, and whether the current viewer liked it."""
        cursor = get_db().cursor(dictionary=True)

        #1. Count the total likes for the post
        cursor.execute("SELECT COUNT(*) as count FROM likes WHERE post_id = %s", (post_id,))
        like_count = cursor.fetchone()['count']

        #2. Check whether the current logged-in user liked the post
        liked_by_me = False
        user_id = current_user_id()
        if user_id is not None:
            cursor.execute(
                "SELECT 1 FROM likes WHERE post_id = %s AND user_id = %s",
                (post_id, user_id),
            )
            liked_by_me = cursor.fetchone() is not None # True if the user liked the post, False otherwise
        cursor.close()
        return jsonify({'like_count': like_count, 'liked_by_me': liked_by_me}), 200



# ═════════════════════════════════════════════════════════════════════════════
# Moderation routes (reporting)
# ═════════════════════════════════════════════════════════════════════════════

@app.route('/api/posts/<int:post_id>/report', methods=['POST'])
def report_post(post_id):
    """Let a logged-in user flag a post for moderator review."""
    reporter_id = current_user_id()
    if reporter_id is None:
        return jsonify({'message': 'Unauthorized'}), 401

    reason = request.get_json().get('reason', '').strip()
    if not reason:
        return jsonify({'message': 'A reason is required'}), 400

    try:
        cursor = get_db().cursor()
        cursor.execute(
            "INSERT INTO reports (post_id, reporter_id, reason) VALUES (%s, %s, %s)",
            (post_id, reporter_id, reason),
        )
        get_db().commit()
        cursor.close()
        return jsonify({'message': 'Post reported successfully'}), 201

    except mysql.connector.Error as err:
        if err.errno == ERR_DUPLICATE_ENTRY:
            return jsonify({'message': 'You already reported this post'}), 400
        if err.errno == ERR_FOREIGN_KEY:
            return jsonify({'message': 'Post does not exist'}), 404
        return jsonify({'message': 'Database error occurred'}), 500


@app.route('/api/admin/reports', methods=['GET'])
@roles_required('admin', 'moderator')
def list_reports():
    """All open reports, newest first, with post and reporter details."""
    cursor = get_db().cursor(dictionary=True)
    cursor.execute(
        """
        SELECT reports.id, reports.reason, reports.status, reports.created_at,
               posts.id AS post_id, posts.title AS post_title,
               author.id AS author_id, author.name AS author_name,
               reporter.name AS reporter_name
        FROM reports
        JOIN posts ON reports.post_id = posts.id
        JOIN users AS author ON posts.author_id = author.id
        JOIN users AS reporter ON reports.reporter_id = reporter.id
        WHERE reports.status = 'open'
        ORDER BY reports.created_at DESC
        """
    )
    results = serialize_timestamps(cursor.fetchall())
    cursor.close()
    return jsonify(results), 200


@app.route('/api/admin/posts/<int:post_id>', methods=['DELETE'])
@roles_required('admin', 'moderator')
def admin_delete_post(post_id):
    """Remove a post. Its likes, comments and reports go with it (ON DELETE CASCADE)."""
    cursor = get_db().cursor()
    cursor.execute("DELETE FROM posts WHERE id = %s", (post_id,))
    deleted = cursor.rowcount
    get_db().commit()
    cursor.close()

    if deleted == 0:
        return jsonify({'message': 'Post not found'}), 404
    return jsonify({'message': 'Post deleted successfully'}), 200


@app.route('/api/admin/reports/<int:report_id>', methods=['PUT'])
@roles_required('admin', 'moderator')
def update_report_status(report_id):
    """Mark a report as 'resolved' (action taken) or 'dismissed' (no action needed)."""
    new_status = request.get_json().get('status', '').strip()
    if new_status not in ('resolved', 'dismissed'):
        return jsonify({'message': "Status must be 'resolved' or 'dismissed'"}), 400

    cursor = get_db().cursor()
    cursor.execute("UPDATE reports SET status = %s WHERE id = %s", (new_status, report_id))
    updated = cursor.rowcount
    get_db().commit()
    cursor.close()

    if updated == 0:
        return jsonify({'message': 'Report not found'}), 404
    return jsonify({'message': f'Report marked as {new_status}'}), 200


@app.route('/api/admin/users/<int:user_id>/ban', methods=['POST'])
@roles_required('admin')
def ban_user(user_id):
    """Ban a user and kill their active session. Admins only, not moderators."""
    if current_user_id() == user_id:
        return jsonify({'message': 'You cannot ban yourself'}), 400

    cursor = get_db().cursor()
    cursor.execute("UPDATE users SET is_banned = TRUE WHERE id = %s", (user_id,))
    updated = cursor.rowcount
    # Log them out immediately instead of waiting for the session to expire
    cursor.execute("DELETE FROM sessions WHERE user_id = %s", (user_id,))
    get_db().commit()
    cursor.close()

    if updated == 0:
        return jsonify({'message': 'User not found'}), 404
    return jsonify({'message': 'User banned successfully'}), 200


@app.route('/api/admin/users/<int:user_id>/unban', methods=['POST'])
@roles_required('admin')
def unban_user(user_id):
    """Lift a ban."""
    cursor = get_db().cursor()
    cursor.execute("UPDATE users SET is_banned = FALSE WHERE id = %s", (user_id,))
    updated = cursor.rowcount
    get_db().commit()
    cursor.close()

    if updated == 0:
        return jsonify({'message': 'User not found'}), 404
    return jsonify({'message': 'User unbanned successfully'}), 200


#getting the comments for post
@app.route('/api/user-posts/<int:post_id>/comments', methods=['GET'])
def get_post_comments(post_id):
    """Get all comments for a specific post."""
    cursor = get_db().cursor(dictionary=True)
    query = """
        SELECT comments.id, comments.content, comments.created_at,
               users.id as user_id, users.name as user_name, users.profile_picture_url
        FROM comments
        JOIN users ON comments.user_id = users.id
        WHERE comments.post_id = %s
        ORDER BY comments.created_at ASC
    """
    cursor.execute(query, (post_id,))
    results = serialize_timestamps(cursor.fetchall())
    cursor.close()
    return jsonify(results), 200

# ═════════════════════════════════════════════════════════════════════════════
# Social routes (add comment / get comments)
# ═════════════════════════════════════════════════════════════════════════════

@app.route('/api/user-posts/<int:post_id>/comments', methods=['POST'])
def add_comment(post_id):
    """
    Add a new comment to a specific post.
    Only logged-in users can comment.
    """
    # 1. Make sure the user is logged in
    user_id = current_user_id()
    if user_id is None:
        return jsonify({'message': 'Unauthorized - Please log in to comment'}), 401

    # 2. Get the comment text from the request body (JSON)
    data = request.get_json()
    content = data.get('content', '').strip()

    # Make sure the comment isn't empty
    if not content:
        return jsonify({'message': 'Comment content is required'}), 400

    # 3. Save the comment to the database
    cursor = get_db().cursor()
    query = "INSERT INTO comments (user_id, post_id, content) VALUES (%s, %s, %s)"

    try:
        cursor.execute(query, (user_id, post_id, content))
        get_db().commit()
        cursor.close()
        return jsonify({'message': 'Comment added successfully'}), 201
    except mysql.connector.Error as err:
        cursor.close()
        return jsonify({'message': f'Database error: {err}'}), 500



if __name__ == '__main__':
    # PORT env var lets you avoid clashes (e.g. macOS AirPlay uses 5000)
    app.run(debug=True, port=int(os.getenv('PORT', 5001)), host='0.0.0.0')
