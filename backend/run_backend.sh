#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

# Install requirements only if not already installed
if [ ! -f .requirements_installed ]; then
    python3 -m pip install -r requirements.txt
    touch .requirements_installed
    echo "Requirements installed."
else
    echo "Requirements already installed, skipping."
fi

# Run seed.py only if it hasn't been run before
if [ ! -f .seeded ]; then
    python3 seed.py
    touch .seeded
    echo "Database seeded."
else
    echo "Database already seeded, skipping."
fi

python3 server.py
