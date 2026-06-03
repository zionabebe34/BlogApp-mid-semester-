#!/usr/bin/env bash
#
# BlogApp — single startup script
#
# Usage:
#   ./start.sh              # set up everything and start both servers
#   ./start.sh --seed       # seed the database, then start both servers
#   ./start.sh --seed-only  # seed the database only (no servers)
#
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
VENV_DIR="$BACKEND_DIR/.venv"
PYTHON="$VENV_DIR/bin/python"

SEED=false
SEED_ONLY=false
for arg in "$@"; do
    case "$arg" in
        --seed)      SEED=true ;;
        --seed-only) SEED=true; SEED_ONLY=true ;;
    esac
done

# ── 1. Python virtualenv + requirements ───────────────────────────────────────
echo "==> Setting up Python backend..."
if [ ! -d "$VENV_DIR" ]; then
    echo "    Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi
"$PYTHON" -m pip install --quiet --upgrade pip
"$PYTHON" -m pip install --quiet -r "$BACKEND_DIR/requirements.txt"
echo "    Backend dependencies ready."

# ── 2. Create database + tables if they don't exist ───────────────────────────
echo "==> Initialising database..."
MYSQL_PWD="$(cd "$BACKEND_DIR" && "$PYTHON" -c "from password import your_password; print(your_password)")"
mysql -u root -p"$MYSQL_PWD" <<'SQL'
CREATE DATABASE IF NOT EXISTS homework_5;
USE homework_5;

CREATE TABLE IF NOT EXISTS users (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    name                VARCHAR(255)        NOT NULL,
    email               VARCHAR(255)        NOT NULL UNIQUE,
    password            VARCHAR(255)        NOT NULL,
    bio                 TEXT,
    profile_picture_url TEXT,
    created_at          DATETIME            DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sessions (
    user_id     INT          NOT NULL UNIQUE,
    session_id  VARCHAR(255) NOT NULL,
    created_at  DATETIME     DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS posts (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    author_id   INT          NOT NULL,
    title       VARCHAR(255) NOT NULL,
    body        TEXT         NOT NULL,
    image_url   TEXT,
    created_at  DATETIME     DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS follows (
    follower_id INT NOT NULL,
    followed_id INT NOT NULL,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (follower_id, followed_id),
    FOREIGN KEY (follower_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (followed_id) REFERENCES users(id) ON DELETE CASCADE
);
SQL
echo "    Database ready."

# ── 3. Seed the database ───────────────────────────────────────────────────────
if [ "$SEED" = true ]; then
    echo "==> Seeding database..."
    (cd "$BACKEND_DIR" && "$PYTHON" seed.py)
    echo "    Database seeded."
fi

if [ "$SEED_ONLY" = true ]; then
    echo "==> Done."
    exit 0
fi

# ── 4. Frontend npm dependencies ──────────────────────────────────────────────
echo "==> Setting up frontend..."
if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
    echo "    Installing npm dependencies..."
    (cd "$FRONTEND_DIR" && npm install)
else
    echo "    node_modules already present, skipping npm install."
fi

# ── 5. Start both servers ─────────────────────────────────────────────────────
cleanup() {
    echo ""
    echo "==> Shutting down..."
    if [ -n "${BACKEND_PID:-}" ] && kill -0 "$BACKEND_PID" 2>/dev/null; then
        kill "$BACKEND_PID" 2>/dev/null || true
    fi
}
trap cleanup EXIT INT TERM

echo "==> Starting Flask backend  →  http://localhost:5000"
(cd "$BACKEND_DIR" && "$PYTHON" server.py) &
BACKEND_PID=$!

echo "==> Starting Vite frontend  →  http://localhost:5173"
echo "    Press Ctrl+C to stop both servers."
(cd "$FRONTEND_DIR" && npm run dev)
