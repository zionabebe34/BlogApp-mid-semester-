# Blog App — Fullstack Assignment mid-semester project

A full-stack social blog application built with **React + Flask + MySQL**.

Users can sign up, write rich-text posts with images, follow each other, search for
people, and browse both a global feed and a personalized "following" feed.

---

## Environment Setup

Before running the backend (or its tests), copy the template to create your
own `config.env`:

```bash
cd backend
cp config.env.example config.env
```

Then open `backend/config.env` and fill in your own local MySQL details:

```
DB_HOST=
DB_USER=
DB_PASSWORD=
DB_NAME=
```

This file is required for `server.py` — and for `pytest` — to connect to
your database. It's gitignored, so it's never committed once you fill it in.

---

## Tech Stack

| Layer     | Technology                                      |
|-----------|-------------------------------------------------|
| Frontend  | React 19, Vite, Material UI (MUI), React Router |
| Editor    | react-quill-new (WYSIWYG rich text)             |
| Backend   | Python, Flask, flask-cors                       |
| Database  | MySQL (connection pool)                         |
| Auth      | bcrypt, UUID sessions, HTTP cookies             |

---

## Features

- **Authentication** — sign-up, login, logout with bcrypt-hashed passwords and cookie sessions.
- **User profiles** — a dedicated page per user showing name, bio, profile picture, follower/following counts, and their posts.
- **My Profile** — your own page with an inline **bio editor** and clickable **followers / following** lists (open a dialog, click a user to visit their profile).
- **Follow / Unfollow** — build relationships between accounts; counts shown on profiles.
- **Search** — find users by name or email, with debounced input calling a `LIKE`-based search API.
- **Feed** — two tabs:
  - **Global feed** — posts from everyone, with **infinite scroll** (lazy loading via `limit`/`offset`).
  - **Following feed** — posts only from people you follow.
- **Posts** — create posts with a **rich-text editor** (bold, italics, underline, lists, links) and an optional **image**.
- **Time-ago timestamps** — posts show "2 hours ago" style relative times.
- **Hover-to-expand** post cards — full content reveals on mouse hover.

---

## Project Structure

```
BlogApp/
├── start.sh                 # One-command setup + run (backend + frontend)
├── backend/
│   ├── server.py            # Flask API server (MySQL connection pool)
│   ├── seed.py              # Seeds users, posts, and random follow relationships
│   ├── requirements.txt     # Python dependencies
│   └── password.py          # Your local MySQL password — edit before running
└── frontend/
    ├── index.html
    ├── vite.config.js       # Vite proxy to Flask
    ├── package.json
    ├── public/
    └── src/
        ├── App.jsx          # Routes + global auth state
        ├── api.js           # Shared fetch helpers
        ├── utils/
        │   └── timeAgo.js   # Relative "time ago" formatter
        ├── components/
        │   ├── TopBar.jsx       # Navigation bar with login/logout
        │   └── SinglePost.jsx   # Post card (image, time-ago, hover expand)
        └── pages/
            ├── Feed.jsx          # Global + Following tabs, infinite scroll
            ├── NewPost.jsx       # Create a post — rich text + image (protected)
            ├── Login.jsx
            ├── Signup.jsx
            ├── UsersPage.jsx     # All users + debounced search
            ├── UserPostsPage.jsx # Public profile (bio, picture, posts, follow)
            ├── MyProfilePage.jsx # Own profile (edit bio, followers/following lists)
            └── About.jsx
```

---

## How to Run

### Step 1 — Install MySQL (required before anything else)

The app needs a running MySQL server on your machine. If you don't have it installed:

- **Mac (Homebrew):**
  ```bash
  brew install mysql
  brew services start mysql
  ```
- **Windows:** Download the installer from [mysql.com/downloads](https://dev.mysql.com/downloads/installer/)
- **Linux (Ubuntu/Debian):**
  ```bash
  sudo apt install mysql-server
  sudo systemctl start mysql
  ```

Make sure MySQL is running and that you know your **root password** before continuing.

---

### Step 2 — Set your MySQL password

Open `backend/password.py` and replace the placeholder with your MySQL root password:

```python
your_password = 'YOUR_MYSQL_PASSWORD'
```

---

### Step 3 — First-time setup (run this once)

```bash
./start.sh --seed
```

This single command handles everything:

1. Creates a Python virtual environment and installs all backend dependencies
2. Creates the `homework_5` database and all tables automatically
3. Seeds the database with sample users, posts, and follow relationships (pulled from JSONPlaceholder)
4. Installs frontend npm dependencies
5. Starts **Flask** on `http://localhost:5000` and **Vite** on `http://localhost:5173`

Press **Ctrl+C** to stop both servers.

---

### Step 4 — Every run after the first

```bash
./start.sh
```

No need to seed again — your data is already there.

---

### Other options

```bash
./start.sh --seed-only  # re-seed the database without starting the servers
```

> The Vite proxy forwards all `/api/*` requests to Flask automatically — no CORS issues.

---

## Before Running Tests

The backend has two kinds of tests:

- **Unit tests** (`backend/test_auth.py`) — mock the database, no MySQL required.
- **Integration tests** (`backend/test_auth_integration.py`) — hit a **real MySQL
  database**, because `server.py` opens a live connection pool the moment it's
  imported (see `connection_pool = pooling.MySQLConnectionPool(...)` in `server.py`).

If MySQL isn't set up and running with matching credentials, the integration
tests fail immediately — the import of `server` itself throws a connection
error before a single test runs.

### Steps

1. Make sure MySQL is installed and running (see **Step 1** above).
2. Set your MySQL root password in `backend/password.py`:
   ```python
   your_password = 'YOUR_MYSQL_PASSWORD'
   ```
3. Create the database and tables (you don't need to seed data — the tests
   create their own users):
   ```bash
   ./start.sh --seed-only
   ```
4. Install dependencies and run the tests from `backend/`:
   ```bash
   cd backend
   pip install -r requirements.txt
   python3 -m pytest -v
   ```

   To run just one file:
   ```bash
   python3 -m pytest test_auth.py -v              # unit tests, no DB needed
   python3 -m pytest test_auth_integration.py -v   # integration tests, needs MySQL
   ```

---

## Database Schema

```sql
CREATE TABLE users (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    name                VARCHAR(255)        NOT NULL,
    email               VARCHAR(255)        NOT NULL UNIQUE,
    password            VARCHAR(255)        NOT NULL,
    bio                 TEXT,
    profile_picture_url TEXT,
    created_at          DATETIME            DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE sessions (
    user_id     INT          NOT NULL UNIQUE,
    session_id  VARCHAR(255) NOT NULL,
    created_at  DATETIME     DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE posts (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    author_id   INT          NOT NULL,
    title       VARCHAR(255) NOT NULL,
    body        TEXT         NOT NULL,
    image_url   TEXT,
    created_at  DATETIME     DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE follows (
    follower_id INT NOT NULL,
    followed_id INT NOT NULL,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (follower_id, followed_id),
    FOREIGN KEY (follower_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (followed_id) REFERENCES users(id) ON DELETE CASCADE
);
```

> You don't need to run this manually — `start.sh` creates all tables automatically.

---

## API Endpoints

| Method | Endpoint                          | Auth required | Description                                   |
|--------|-----------------------------------|---------------|-----------------------------------------------|
| POST   | `/api/signup`                     | No            | Register a new user (starts with 0 follows)   |
| POST   | `/api/login`                      | No            | Login, sets session cookie                    |
| POST   | `/api/logout`                     | No            | Logout, clears session                        |
| GET    | `/api/me`                         | Cookie        | Returns current logged-in user                |
| PUT    | `/api/me/bio`                     | Yes           | Update your own bio                           |
| GET    | `/api/feed?limit=&offset=`        | No            | Global feed, paginated                        |
| GET    | `/api/feed/following`             | Yes           | Posts from users you follow                   |
| POST   | `/api/new-post`                   | Yes           | Create a post (title, body HTML, image_url)   |
| GET    | `/api/users`                      | No            | All users with post counts                    |
| GET    | `/api/users/search?q=`            | No            | Search users by name or email                 |
| GET    | `/api/user-posts/:id`             | No            | Posts by a specific user                      |
| GET    | `/api/users/:id/profile`          | No            | Full profile: bio, picture, counts, posts     |
| GET    | `/api/users/:id/followers`        | No            | List of users who follow this user            |
| GET    | `/api/users/:id/following`        | No            | List of users this user follows               |
| POST   | `/api/users/:id/follow`           | Yes           | Follow a user                                 |
| POST   | `/api/users/:id/unfollow`         | Yes           | Unfollow a user                               |

---

## Notes

- **Connection pool** — the backend uses a MySQL connection pool (one connection
  per request) instead of a single shared connection. This prevents the native
  driver from crashing when Flask handles concurrent requests on multiple threads.
- **Seeding & follows** — `seed.py` pulls demo users and posts from
  JSONPlaceholder and generates random follow relationships among them. Re-running
  it resets the `follows` table. **New users who sign up later start with 0
  followers and 0 following.**
- **Rich text** — post bodies are stored as HTML from the WYSIWYG editor and
  rendered with `dangerouslySetInnerHTML`. For production, sanitizing this HTML
  (e.g. with DOMPurify) is recommended to prevent XSS.

---

## Authentication Flow

1. **Signup** — password is hashed with bcrypt before saving to DB.
2. **Login** — bcrypt verifies the password, a UUID `session_id` is generated, saved in the `sessions` table, and sent as an HTTP cookie.
3. **Protected routes** — pages like `/new-post` and `/profile` redirect to `/Login` if not logged in.
4. **Page refresh** — on load, `App.jsx` calls `/api/me`, which reads the cookie and restores the logged-in state.
5. **Logout** — the session row is deleted from the DB and the cookie is cleared.

---

## Author

Zion Abebe
