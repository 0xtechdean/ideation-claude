#!/bin/bash
# Sync current branch to private repository

set -e

BRANCH=$(git branch --show-current)
echo "Syncing $BRANCH to private repository..."

git push private "$BRANCH"
echo "✓ Pushed to private repository"
