# Blog App — Fullstack Assignment mid-semester project

A full-stack social blog application built with **React + Flask + MySQL**.

Users can sign up, write rich-text posts with images, follow each other, search for
people, and browse both a global feed and a personalized "following" feed.

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
├── start.sh             # One-command setup + run (backend + frontend)
├── backend/
│   ├── server.py        # Flask API server (MySQL connection pool)
│   ├── seed.py          # Seeds users, posts, and random follow relationships
│   ├── requirements.txt # Python dependencies
│   ├── run_backend.sh   # Backend-only setup/run helper
│   └── password.py      # Your local MySQL password (not committed)
├── src/
│   ├── App.jsx          # Routes + global auth state
│   ├── api.js           # Shared fetch helpers
│   ├── utils/
│   │   └── timeAgo.js   # Relative "time ago" formatter
│   ├── components/
│   │   ├── TopBar.jsx   # Navigation bar with login/logout
│   │   └── SinglePost.jsx   # Post card (image, time-ago, hover expand)
│   └── pages/
│       ├── Feed.jsx          # Global + Following tabs, infinite scroll
│       ├── NewPost.jsx       # Create a post — rich text + image (protected)
│       ├── Login.jsx
│       ├── Signup.jsx
│       ├── UsersPage.jsx     # All users + debounced search
│       ├── UserPostsPage.jsx # Public profile (bio, picture, posts, follow)
│       ├── MyProfilePage.jsx # Own profile (edit bio, followers/following lists)
│       └── About.jsx
└── vite.config.js       # Vite proxy to Flask
```

---

## Database Schema

```sql
CREATE TABLE users (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    name                VARCHAR(255),
    email               VARCHAR(255) UNIQUE NOT NULL,
    password            VARCHAR(255) NOT NULL,
    bio                 TEXT,
    profile_picture_url VARCHAR(512)
);

CREATE TABLE posts (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    title      VARCHAR(255) NOT NULL,
    body       TEXT NOT NULL,
    image_url  VARCHAR(512),
    author_id  INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (author_id) REFERENCES users(id)
);

CREATE TABLE sessions (
    user_id    INT NOT NULL UNIQUE,
    session_id VARCHAR(255) NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE follows (
    follower_id INT NOT NULL,
    followed_id INT NOT NULL,
    PRIMARY KEY (follower_id, followed_id),
    FOREIGN KEY (follower_id) REFERENCES users(id),
    FOREIGN KEY (followed_id) REFERENCES users(id)
);
```

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

## How to Run

### Quick start (recommended)

From the project root:

```bash
./start.sh          # install deps + run backend and frontend together
./start.sh --seed   # also (re)seed the database first
```

This creates a Python virtualenv, installs `backend/requirements.txt`, runs
`npm install` if needed, then starts **Flask** (`http://localhost:5000`) and
**Vite** (`http://localhost:5173`) together. Press **Ctrl+C** to stop both.

> Requires MySQL to already be running with the `homework_5` database and a
> valid `backend/password.py`. The script does not start MySQL.

### Manual steps

**1. Database**

```sql
CREATE DATABASE homework_5;
USE homework_5;
-- then create the tables above
```

Seed with sample users, posts, and random follow relationships:

```bash
cd backend
python seed.py
```

**2. Backend**

```bash
cd backend
pip install -r requirements.txt
python server.py        # http://127.0.0.1:5000
```

**3. Frontend**

```bash
npm install
npm run dev             # http://localhost:5173
```

> The Vite proxy forwards all `/api/*` requests to Flask automatically — no CORS issues.

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
