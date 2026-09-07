#inserting placeholder data into database
import string
import mysql.connector
import bcrypt
import random
import requests
from password import your_password  # Import the password variable from password.py


conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password=your_password,
    database='homework_5'
) 

#random password generator
def generate_random_password(length=10):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


cursor = conn.cursor()

#fetch from jsonplaceholder
users = requests.get('https://jsonplaceholder.typicode.com/users').json()

for user in users:
    # 1. Extract the catchPhrase from company to use as the bio
    bio_text = user.get('company', {}).get('catchPhrase', 'No bio available.')

    # 2. Build an avatar URL from DiceBear based on the username
    username_seed = user.get('username', 'default')
    avatar_url = f"https://api.dicebear.com/7.x/avataaars/svg?seed={username_seed}"

    # 3. Generate a password and hash it
    plain_password = generate_random_password()
    hashed_password = bcrypt.hashpw(plain_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # Updated insert query with profile_picture_url
    query = """
        INSERT INTO users (name, email, password, bio, profile_picture_url) 
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE 
            bio = VALUES(bio),
            profile_picture_url = VALUES(profile_picture_url)
    """
    
    cursor.execute(query, (user['name'], user['email'], hashed_password, bio_text, avatar_url))

conn.commit()
print("Users populated/updated with bio and profile pictures successfully!")

# Fetch posts from the API and insert them into the table
posts = requests.get('https://jsonplaceholder.typicode.com/posts').json()

for post in posts:
    cursor.execute("INSERT IGNORE INTO posts (author_id, title, body) VALUES (%s, %s, %s)", (post['userId'], post['title'], post['body']))
conn.commit()

# ── Random follow relationships ───────────────────────────────────────────────
# Give the existing (seeded) users a random set of followers/following so the
# profile pages show realistic numbers. New users who sign up later start at 0
# because the signup endpoint never creates follow rows.

# Start from a clean slate so re-running this script doesn't pile up duplicates.
cursor.execute("DELETE FROM follows")

# Get the ids of all current users
cursor.execute("SELECT id FROM users")
user_ids = [row[0] for row in cursor.fetchall()]

for follower_id in user_ids:
    # Everyone else this user could possibly follow
    candidates = [uid for uid in user_ids if uid != follower_id]

    # Follow a random number of them (between 0 and ~70% of the others)
    if candidates:
        k = random.randint(0, max(1, int(len(candidates) * 0.7)))
        followed_users = random.sample(candidates, k)

        for followed_id in followed_users:
            cursor.execute(
                "INSERT IGNORE INTO follows (follower_id, followed_id) VALUES (%s, %s)",
                (follower_id, followed_id)
            )

conn.commit()
print("Random follow relationships created successfully!")

# ==========================================
# ── Seeding Comments and Likes ────────────
# ==========================================
print("Seeding comments and likes...")

# 1. Fetch the ids of all existing posts
cursor.execute("SELECT id FROM posts")
post_ids = [row[0] for row in cursor.fetchall()]

# (we reuse the user_ids fetched earlier in the script for the followers)

# 2. Build a list of fake comments suited to our DIY project
fake_comments = [
    "Wow, this looks amazing! Great job.",
    "Can you share the list of materials you used?",
    "I need to try this on the weekend!",
    "Love the colors. Very creative.",
    "How long did this take to build?",
    "Not bad, but I would have used different wood.",
    "Thanks for the inspiration!",
    "My attempt at this was a total disaster 😂"
]

# 3. Loop over every post and insert likes and comments
for post_id in post_ids:

    # --- Insert comments ---
    # Pick a random number of comments per post (e.g. between 0 and 3)
    num_comments = random.randint(0, 3)
    for _ in range(num_comments):
        random_user_id = random.choice(user_ids)  # pick a random user to comment
        random_content = random.choice(fake_comments)  # pick random text from the list

        cursor.execute(
            "INSERT INTO comments (user_id, post_id, content) VALUES (%s, %s, %s)",
            (random_user_id, post_id, random_content)
        )

    # --- Insert likes ---
    # Pick how many likes the post will have (between 0 and 8 likes)
    num_likes = random.randint(0, min(8, len(user_ids)))

    # Use random.sample to pick unique users (no duplicates)
    likers = random.sample(user_ids, num_likes)

    for liker_id in likers:
        cursor.execute(
            "INSERT IGNORE INTO likes (user_id, post_id) VALUES (%s, %s)",
            (liker_id, post_id)
        )

# 4. Commit all changes to the database
conn.commit()
print("Comments and likes created successfully!")

cursor.close()
conn.close()
print("Data inserted successfully!")