from flask import Flask, request, jsonify, make_response, g
from flask_cors import CORS
import bcrypt
import mysql.connector
from mysql.connector import pooling
import uuid
from password import your_password  # Import the password variable from password.py

#import env variables from .env file
from dotenv import load_dotenv
import os

load_dotenv('config.env')



app = Flask(__name__)
CORS(app, origins=['http://localhost:5173', 'http://127.0.0.1:5173', 'http://localhost:3000'], supports_credentials=True)

# Database connection
your_password = your_password  # Use the imported password variable

# A single shared connection is NOT safe across Flask's worker threads:
# concurrent requests using the same MySQL connection crash the C driver
# (double-free in SSL_free). Instead we use a pool and hand each request
# its own connection, returning it when the request ends.
#configur
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

# ── Signup ──────────────────────────────────────────────────────────────────
@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password_plain = data.get('password')

    if not name or not email or not password_plain:
        return jsonify({"error": "Missing required fields"}), 400

    # 1. Generate a unique user avatar link from DiceBear based on their email address
    # (Using email because it is always UNIQUE in the system)
    avatar_url = f"https://api.dicebear.com/7.x/avataaars/svg?seed={email}"
    
    # Initial default biography for a new user
    default_bio = "Hello, I am new to BlogApp!"

    # 2. Hash the password using bcrypt and decode to string
    hashed_password = bcrypt.hashpw(password_plain.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    try:
        
        cursor = get_db().cursor()
        
        # 3. Updated insert query including bio and profile_picture_url exactly like the DB schema
        query = """
            INSERT INTO users (name, email, password, bio, profile_picture_url) 
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (name, email, hashed_password, default_bio, avatar_url))
        get_db().commit()
        cursor.close()

        return jsonify({"message": "User registered successfully!"}), 201

    except mysql.connector.Error as err:
        if err.errno == 1062:  # Duplicate Entry error (e.g., if the email is already registered)
            return jsonify({"error": "Email already exists"}), 400
        return jsonify({"error": "Database error occurred"}), 500

# ── Login ────────────────────────────────────────────────────────────────────
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    cursor = get_db().cursor()
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()

    if not user:
        return jsonify({'message': 'Invalid email or password'}), 401

    # user columns: id, name, email, password
    if not bcrypt.checkpw(password.encode('utf-8'), user[3].encode('utf-8')):
        return jsonify({'message': 'Invalid email or password'}), 401

    # Generate a unique session_id and save it to the sessions table
    session_id = str(uuid.uuid4())
    cursor.execute(
        "INSERT INTO sessions (user_id, session_id) VALUES (%s, %s) ON DUPLICATE KEY UPDATE session_id = %s",
        (user[0], session_id, session_id)
    )
    get_db().commit()

    # Send session_id as a cookie
    response = make_response(jsonify({'message': 'Login successful', 'email': email, 'name': user[1]}))
    response.set_cookie('session_id', session_id, httponly=True, samesite='Lax')
    return response, 200

# ── Logout ───────────────────────────────────────────────────────────────────
@app.route('/api/logout', methods=['POST'])
def logout():
    session_id = request.cookies.get('session_id')
    if session_id:
        cursor = get_db().cursor()
        cursor.execute("DELETE FROM sessions WHERE session_id = %s", (session_id,))
        get_db().commit()

    response = make_response(jsonify({'message': 'Logout successful'}))
    response.delete_cookie('session_id')
    return response, 200

# ── Me (check who is logged in) ───────────────────────────────────────────────
@app.route('/api/me', methods=['GET'])
def me():
    session_id = request.cookies.get('session_id')
    if not session_id:
        return jsonify({'message': 'Not logged in'}), 401

    cursor = get_db().cursor()
    cursor.execute("""
        SELECT users.id, users.name, users.email
        FROM sessions
        JOIN users ON sessions.user_id = users.id
        WHERE sessions.session_id = %s
    """, (session_id,))
    user = cursor.fetchone()

    if not user:
        return jsonify({'message': 'Invalid session'}), 401

    return jsonify({'id': user[0], 'name': user[1], 'email': user[2]}), 200

# ── Update My Bio ─────────────────────────────────────────────────────────────
@app.route('/api/me/bio', methods=['PUT'])
def update_my_bio():
    # Only a logged-in user can edit their own bio
    session_id = request.cookies.get('session_id')
    if not session_id:
        return jsonify({'message': 'Unauthorized'}), 401

    cursor = get_db().cursor()
    cursor.execute("SELECT user_id FROM sessions WHERE session_id = %s", (session_id,))
    session_row = cursor.fetchone()
    if not session_row:
        cursor.close()
        return jsonify({'message': 'Unauthorized'}), 401

    user_id = session_row[0]
    data = request.get_json()
    new_bio = data.get('bio', '')

    cursor.execute("UPDATE users SET bio = %s WHERE id = %s", (new_bio, user_id))
    get_db().commit()
    cursor.close()

    return jsonify({'message': 'Bio updated successfully', 'bio': new_bio}), 200

# ── Global Feed (with Pagination) ───────────────────────────────────────────
@app.route('/api/feed', methods=['GET'])
def feed():
    # 1. Get limit and offset from query parameters (default to 10 and 0)
    limit = int(request.args.get('limit', 10))
    offset = int(request.args.get('offset', 0))
    
    cursor = get_db().cursor(dictionary=True)
    
    # 2. Use SQL LIMIT and OFFSET for efficient lazy loading
    # We also order by creation time so the newest posts appear first
    query = """
        SELECT posts.id, posts.title, posts.body, posts.image_url, posts.created_at,
               users.name as author_name, users.email as author_email, users.profile_picture_url
        FROM posts
        JOIN users ON posts.author_id = users.id
        ORDER BY posts.created_at DESC
        LIMIT %s OFFSET %s
    """
    
    cursor.execute(query, (limit, offset))
    results = cursor.fetchall()
    
    # Format timestamps for JSON
    for post in results:
        if post['created_at']:
            post['created_at'] = post['created_at'].isoformat()
            
    cursor.close()
    return jsonify(results), 200

# ── New Post ──────────────────────────────────────────────────────────────────
@app.route('/api/new-post', methods=['POST'])
def new_post():
    session_id = request.cookies.get('session_id')
    if not session_id:
        return jsonify({'message': 'Unauthorized'}), 401

    cursor = get_db().cursor()
    cursor.execute("SELECT user_id FROM sessions WHERE session_id = %s", (session_id,))
    session_row = cursor.fetchone()
    if not session_row:
        return jsonify({'message': 'Unauthorized'}), 401

    data = request.get_json()
    title = data.get('title', '').strip()
    body = data.get('body', '')
    image_url = data.get('image_url')
    author_id = session_row[0]

    if not title or not body:
        return jsonify({'message': 'Title and body are required'}), 400

    cursor.execute(
        "INSERT INTO posts (title, body, image_url, author_id) VALUES (%s, %s, %s, %s)",
        (title, body, image_url, author_id)
    )
    get_db().commit()

    return jsonify({'message': 'Post created successfully'}), 201

# ── Users ─────────────────────────────────────────────────────────────────────
@app.route('/api/users', methods=['GET'])
def get_users():
    cursor = get_db().cursor()
    cursor.execute("""
        SELECT users.id, users.name, users.email, COUNT(posts.id) as post_count
        FROM users
        LEFT JOIN posts ON posts.author_id = users.id
        GROUP BY users.id, users.name, users.email
    """)
    results = cursor.fetchall()
    users = []
    for row in results:
        users.append({
            'id': row[0],
            'name': row[1],
            'email': row[2],
            'postCount': row[3]
        })
    return jsonify(users), 200

# ── User Posts ────────────────────────────────────────────────────────────────
@app.route('/api/user-posts/<int:user_id>', methods=['GET'])
def get_user_posts(user_id):
    cursor = get_db().cursor()
    cursor.execute("SELECT name FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    user_name = user[0] if user else f'User #{user_id}'

    cursor.execute("SELECT id, title, body FROM posts WHERE author_id = %s", (user_id,))
    results = cursor.fetchall()
    posts = []
    for row in results:
        posts.append({'id': row[0], 'title': row[1], 'body': row[2]})
    return jsonify({'user_name': user_name, 'posts': posts}), 200

# ── Get User Profile ────────────────────────────────────────────────────────
@app.route('/api/users/<int:user_id>/profile', methods=['GET'])
def get_user_profile(user_id):
    # Use dictionary=True to easily map DB rows to JSON objects
    cursor = get_db().cursor(dictionary=True)

    # 1. Fetch basic user details including bio and profile picture
    cursor.execute("""
        SELECT id, name, email, bio, profile_picture_url
        FROM users WHERE id = %s
    """, (user_id,))
    user = cursor.fetchone()

    # Return 404 if the user does not exist in the database
    if not user:
        cursor.close()
        return jsonify({'message': 'User not found'}), 404

    # 2. Count the number of followers for this user
    cursor.execute("SELECT COUNT(*) as count FROM follows WHERE followed_id = %s", (user_id,))
    followers = cursor.fetchone()['count']

    # 3. Count how many users this person is following
    cursor.execute("SELECT COUNT(*) as count FROM follows WHERE follower_id = %s", (user_id,))
    following = cursor.fetchone()['count']

    # 4. Check if the currently logged-in user is already following this profile
    is_following = False
    session_id = request.cookies.get('session_id')
    if session_id:
        cursor.execute("SELECT user_id FROM sessions WHERE session_id = %s", (session_id,))
        session_row = cursor.fetchone()
        if session_row:
            viewer_id = session_row['user_id']
            cursor.execute(
                "SELECT 1 FROM follows WHERE follower_id = %s AND followed_id = %s",
                (viewer_id, user_id)
            )
            is_following = cursor.fetchone() is not None

    # 5. Fetch all posts authored by this user, ordered by creation time
    cursor.execute("SELECT id, title, body, image_url, created_at FROM posts WHERE author_id = %s ORDER BY created_at DESC", (user_id,))
    posts = cursor.fetchall()
    # Serialize datetimes so jsonify can handle them
    for post in posts:
        if post['created_at']:
            post['created_at'] = post['created_at'].isoformat()

    cursor.close()

    # Combine user data, counts, and posts into a single JSON response
    return jsonify({
        **user,
        'followers_count': followers,
        'following_count': following,
        'is_following': is_following,
        'posts': posts
    }), 200

# ── Followers / Following lists ──────────────────────────────────────────────
@app.route('/api/users/<int:user_id>/followers', methods=['GET'])
def get_followers(user_id):
    # Everyone who follows this user
    cursor = get_db().cursor(dictionary=True)
    cursor.execute("""
        SELECT users.id, users.name, users.email, users.profile_picture_url
        FROM follows
        JOIN users ON follows.follower_id = users.id
        WHERE follows.followed_id = %s
    """, (user_id,))
    results = cursor.fetchall()
    cursor.close()
    return jsonify(results), 200


@app.route('/api/users/<int:user_id>/following', methods=['GET'])
def get_following(user_id):
    # Everyone this user follows
    cursor = get_db().cursor(dictionary=True)
    cursor.execute("""
        SELECT users.id, users.name, users.email, users.profile_picture_url
        FROM follows
        JOIN users ON follows.followed_id = users.id
        WHERE follows.follower_id = %s
    """, (user_id,))
    results = cursor.fetchall()
    cursor.close()
    return jsonify(results), 200

# ── Follow User ──────────────────────────────────────────────────────────────
@app.route('/api/users/<int:user_id>/follow', methods=['POST'])
def follow_user(user_id):
    # Check if the user is authenticated via session cookie
    session_id = request.cookies.get('session_id')
    if not session_id:
        return jsonify({'message': 'Unauthorized'}), 401

    cursor = get_db().cursor()
    # Retrieve the logged-in user's ID from the sessions table
    cursor.execute("SELECT user_id FROM sessions WHERE session_id = %s", (session_id,))
    session_row = cursor.fetchone()
    if not session_row:
        return jsonify({'message': 'Unauthorized'}), 401

    follower_id = session_row[0]
    followed_id = user_id

    # Prevent users from following themselves
    if follower_id == followed_id:
        return jsonify({'message': 'You cannot follow yourself'}), 400

    try:
        # Insert the follow relationship into the database
        cursor.execute(
            "INSERT INTO follows (follower_id, followed_id) VALUES (%s, %s)",
            (follower_id, followed_id)
        )
        get_db().commit()
        cursor.close()
        return jsonify({'message': 'Successfully followed user'}), 200
        
    except mysql.connector.Error as err:
        if err.errno == 1062:  # Duplicate entry error (already following)
            return jsonify({'message': 'You are already following this user'}), 400
        if err.errno == 1452:  # Foreign key constraint failure (user doesn't exist)
            return jsonify({'message': 'User to follow does not exist'}), 404
        return jsonify({'message': 'Database error occurred'}), 500

# ── Unfollow User ────────────────────────────────────────────────────────────
@app.route('/api/users/<int:user_id>/unfollow', methods=['POST'])
def unfollow_user(user_id):
    # Check if the user is authenticated via session cookie
    session_id = request.cookies.get('session_id')
    if not session_id:
        return jsonify({'message': 'Unauthorized'}), 401

    cursor = get_db().cursor()
    # Retrieve the logged-in user's ID from the sessions table
    cursor.execute("SELECT user_id FROM sessions WHERE session_id = %s", (session_id,))
    session_row = cursor.fetchone()
    if not session_row:
        return jsonify({'message': 'Unauthorized'}), 401

    follower_id = session_row[0]
    followed_id = user_id

    try:
        # Delete the follow relationship from the database
        cursor.execute(
            "DELETE FROM follows WHERE follower_id = %s AND followed_id = %s",
            (follower_id, followed_id)
        )
        get_db().commit()
        cursor.close()
        return jsonify({'message': 'Successfully unfollowed user'}), 200
        
    except mysql.connector.Error as err:
        return jsonify({'message': 'Database error occurred'}), 500
    

# ── Search Users ─────────────────────────────────────────────────────────────
@app.route('/api/users/search', methods=['GET'])
def search_users():
    # Get the search query from the URL, e.g., /api/users/search?q=zion
    query = request.args.get('q', '')
    
    # If the search query is empty, return an empty list or all users
    if not query:
        return jsonify([]), 200

    cursor = get_db().cursor(dictionary=True)
    
    # Using SQL LIKE operator to perform a partial match search
    # % is a wildcard in SQL, so %query% means "contains this string"
    search_pattern = f"%{query}%"
    
    cursor.execute("""
        SELECT users.id, users.name, users.email, users.profile_picture_url,
               COUNT(posts.id) as postCount
        FROM users
        LEFT JOIN posts ON posts.author_id = users.id
        WHERE users.name LIKE %s OR users.email LIKE %s
        GROUP BY users.id, users.name, users.email, users.profile_picture_url
    """, (search_pattern, search_pattern))
    
    results = cursor.fetchall()
    cursor.close()
    
    # Return the list of found users
    return jsonify(results), 200

# ── Individual Feed (Posts from followed users) ──────────────────────────────
@app.route('/api/feed/following', methods=['GET'])
def feed_following():
    # 1. Verify that the user is logged in
    session_id = request.cookies.get('session_id')
    if not session_id:
        return jsonify({'message': 'Unauthorized'}), 401

    cursor = get_db().cursor(dictionary=True)
    # Get the logged-in user's ID
    cursor.execute("SELECT user_id FROM sessions WHERE session_id = %s", (session_id,))
    session_row = cursor.fetchone()
    if not session_row:
        cursor.close()
        return jsonify({'message': 'Unauthorized'}), 401

    logged_in_user_id = session_row['user_id']

    # 2. Query posts from users the current user follows
    # We join 'follows' to 'posts' where follows.followed_id = posts.author_id
    query = """
        SELECT posts.id, posts.title, posts.body, posts.image_url, posts.created_at,
               users.name as author_name, users.email as author_email, users.profile_picture_url
        FROM posts
        JOIN follows ON posts.author_id = follows.followed_id
        JOIN users ON posts.author_id = users.id
        WHERE follows.follower_id = %s
        ORDER BY posts.created_at DESC
    """
    
    cursor.execute(query, (logged_in_user_id,))
    results = cursor.fetchall()
    
    # Format timestamps
    for post in results:
        if post['created_at']:
            post['created_at'] = post['created_at'].isoformat()
            
    cursor.close()
    return jsonify(results), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
