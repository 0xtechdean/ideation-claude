#!/bin/bash
# Sync from public repository to private

set -e

BRANCH=$(git branch --show-current)
echo "Syncing from public repository to $BRANCH..."

git fetch origin
git merge origin/"$BRANCH"
git push private "$BRANCH"

echo "✓ Synced from public to private"
