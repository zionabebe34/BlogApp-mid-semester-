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
"""

import os
import uuid

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

    cursor = get_db().cursor()
    cursor.execute("SELECT user_id FROM sessions WHERE session_id = %s", (session_id,))
    row = cursor.fetchone()
    cursor.close()
    return row[0] if row else None


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

    cursor = get_db().cursor()
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()  # columns: id, name, email, password, ...

    if not user:
        return jsonify({'message': 'Invalid email or password'}), 401

    if not bcrypt.checkpw(password.encode('utf-8'), user[3].encode('utf-8')):
        return jsonify({'message': 'Invalid email or password'}), 401

    # Create a fresh session id (replacing any previous one for this user)
    session_id = str(uuid.uuid4())
    cursor.execute(
        "INSERT INTO sessions (user_id, session_id) VALUES (%s, %s) "
        "ON DUPLICATE KEY UPDATE session_id = %s",
        (user[0], session_id, session_id),
    )
    get_db().commit()

    # The cookie is how the browser proves who it is on future requests
    response = make_response(jsonify({'message': 'Login successful', 'email': email, 'name': user[1]}))
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


@app.route('/api/me', methods=['GET'])
def me():
    """Tell the frontend who is currently logged in (id, name, email)."""
    session_id = request.cookies.get('session_id')
    if not session_id:
        return jsonify({'message': 'Not logged in'}), 401

    cursor = get_db().cursor()
    cursor.execute(
        """
        SELECT users.id, users.name, users.email
        FROM sessions
        JOIN users ON sessions.user_id = users.id
        WHERE sessions.session_id = %s
        """,
        (session_id,),
    )
    user = cursor.fetchone()

    if not user:
        return jsonify({'message': 'Invalid session'}), 401

    return jsonify({'id': user[0], 'name': user[1], 'email': user[2]}), 200


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
