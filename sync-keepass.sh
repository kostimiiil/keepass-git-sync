#!/usr/bin/env bash
# sync-keepass.sh
# Works on Linux and Windows (Git Bash)

cd "$(dirname "$0")" || exit 1

# Load configuration or use defaults
CONFIG_FILE="config.json"
if [ -f "$CONFIG_FILE" ]; then
    # Extract database filename from config if jq is available
    if command -v jq >/dev/null 2>&1; then
        DB=$(jq -r '.database.filename // "Passwords.kdbx"' "$CONFIG_FILE")
        COMMIT_FORMAT=$(jq -r '.git.commit_message_format // "Update from {hostname} at {timestamp}"' "$CONFIG_FILE")
        AUTO_PULL=$(jq -r '.git.auto_pull // true' "$CONFIG_FILE")
        AUTO_PUSH=$(jq -r '.git.auto_push // true' "$CONFIG_FILE")
    else
        echo "Warning: jq not found, using default settings"
        DB="Passwords.kdbx"
        COMMIT_FORMAT="Update from {hostname} at {timestamp}"
        AUTO_PULL="true"
        AUTO_PUSH="true"
    fi
else
    echo "No config.json found, using defaults"
    DB="Passwords.kdbx"
    COMMIT_FORMAT="Update from {hostname} at {timestamp}"
    AUTO_PULL="true"
    AUTO_PUSH="true"
fi

echo "Using database: $DB"

# Pull latest from remote (if enabled)
if [ "$AUTO_PULL" = "true" ]; then
    echo "Pulling latest changes..."
    git pull --no-edit
else
    echo "Auto-pull disabled, skipping pull"
fi

# Stage database
git add "$DB"

# Commit only if changes exist
if ! git diff --cached --quiet; then
    # Format commit message
    HOSTNAME=$(hostname)
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    COMMIT_MSG="${COMMIT_FORMAT/{hostname}/$HOSTNAME}"
    COMMIT_MSG="${COMMIT_MSG/{timestamp}/$TIMESTAMP}"
    
    git commit -m "$COMMIT_MSG"
    
    if [ "$AUTO_PUSH" = "true" ]; then
        echo "Pushing changes..."
        git push
    else
        echo "Auto-push disabled, changes committed locally only"
    fi
else
    echo "No changes to commit"
fi
