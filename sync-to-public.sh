#!/bin/bash
# Sync current branch to public repository

set -e

BRANCH=$(git branch --show-current)
echo "Syncing $BRANCH to public repository..."

git push origin "$BRANCH"
echo "✓ Pushed to public repository"
