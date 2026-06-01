#!/usr/bin/env bash
#
# One-command setup + run for BlogApp.
# - Creates a Python virtual environment and installs backend requirements.
# - Installs frontend npm dependencies.
# - Starts the Flask backend and the Vite frontend together.
#
# Usage:
#   ./start.sh          # install deps (first run) and start both servers
#   ./start.sh --seed   # also (re)seed the database before starting
#
set -euo pipefail

# Always run from the directory this script lives in (project root)
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

BACKEND_DIR="$ROOT_DIR/backend"
VENV_DIR="$BACKEND_DIR/.venv"

SEED=false
if [ "${1:-}" = "--seed" ]; then
    SEED=true
fi

# ── 1. Backend: virtualenv + requirements ─────────────────────────────────────
echo "==> Setting up Python backend..."
if [ ! -d "$VENV_DIR" ]; then
    echo "    Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

# Use the venv's python/pip directly (no need to 'activate')
PYTHON="$VENV_DIR/bin/python"
"$PYTHON" -m pip install --quiet --upgrade pip
echo "    Installing backend requirements..."
"$PYTHON" -m pip install --quiet -r "$BACKEND_DIR/requirements.txt"

# Optional database seeding
if [ "$SEED" = true ]; then
    echo "    Seeding database..."
    (cd "$BACKEND_DIR" && "$PYTHON" seed.py)
fi

# ── 2. Frontend: npm dependencies ─────────────────────────────────────────────
echo "==> Setting up frontend..."
if [ ! -d "$ROOT_DIR/node_modules" ]; then
    echo "    Installing npm dependencies..."
    npm install
else
    echo "    node_modules already present, skipping npm install."
fi

# ── 3. Run both servers ───────────────────────────────────────────────────────
# Kill the backend when this script exits (Ctrl+C), so nothing is left running.
cleanup() {
    echo ""
    echo "==> Shutting down..."
    if [ -n "${BACKEND_PID:-}" ] && kill -0 "$BACKEND_PID" 2>/dev/null; then
        kill "$BACKEND_PID" 2>/dev/null || true
    fi
}
trap cleanup EXIT INT TERM

echo "==> Starting Flask backend (http://localhost:5000)..."
(cd "$BACKEND_DIR" && "$PYTHON" server.py) &
BACKEND_PID=$!

echo "==> Starting Vite frontend (http://localhost:5173)..."
echo "    Press Ctrl+C to stop both."
npm run dev

# If 'npm run dev' exits, the trap above stops the backend too.
