#!/bin/bash
set -e

REPO_DIR="/home/benjaminpi2/epaper_display"
SCRIPT="external/main.python3"

echo "Waiting for internet..."

until ping -c1 -W1 8.8.8.8 >/dev/null 2>&1; do
  sleep 2
done

echo "Internet is up"

cd "$REPO_DIR"

echo "Pulling latest code..."
git pull --rebase

echo "Starting epaper script..."
exec /usr/bin/python3 "$REPO_DIR/$SCRIPT"
