# Repository Sync Guide

This project maintains two repositories:

1. **Public Repository**: https://github.com/0xtechdean/ideation-claude
   - Public visibility
   - Code sharing and collaboration
   - GitHub Actions workflows

2. **Private Repository**: https://github.com/Othentic-Ai/ideation-claude-private
   - Private visibility
   - Contains secrets and sensitive evaluations
   - Forked from public repo

## Git Remote Configuration

The repository is configured with the following remotes:

- **`origin`**: Public repository (0xtechdean/ideation-claude)
- **`private`**: Private repository (Othentic-Ai/ideation-claude-private)
- **`upstream`**: Public repository (same as origin, for consistency)

## Syncing Workflows

### Push to Public Repository

```bash
# Push to public repo
git push origin main

# Or push to both
git push origin main && git push private main
```

### Push to Private Repository

```bash
# Push to private repo
git push private main
```

### Sync from Public to Private

```bash
# Fetch latest from public
git fetch origin

# Merge into current branch
git merge origin/main

# Push to private
git push private main
```

### Sync from Private to Public

```bash
# Fetch latest from private
git fetch private

# Merge into current branch
git merge private/main

# Push to public
git push origin main
```

## Recommended Workflow

### For Public Code Changes

1. Make changes locally
2. Commit changes
3. Push to public: `git push origin main`
4. Push to private: `git push private main`

### For Private Evaluations

1. Make changes locally (e.g., add secrets, run evaluations)
2. Commit changes (be careful not to commit secrets!)
3. Push only to private: `git push private main`
4. **Do NOT push to public** if it contains sensitive data

### Syncing Public Updates to Private

If the public repo has updates you want in private:

```bash
# Fetch from public
git fetch origin

# Merge public changes
git merge origin/main

# Push to private
git push private main
```

## Checking Status

```bash
# Check remote status
git remote -v

# Check branch status
git status

# Compare branches
git log origin/main..private/main  # Commits in private but not in public
git log private/main..origin/main   # Commits in public but not in private
```

## Important Notes

⚠️ **Never push secrets to the public repository!**

- The private repo has GitHub Secrets configured
- The public repo should never contain API keys or sensitive data
- Use `.env` files (gitignored) for local development
- Use GitHub Secrets for CI/CD in private repo

## Quick Reference

```bash
# View remotes
git remote -v

# Push to public
git push origin main

# Push to private
git push private main

# Push to both
git push origin main && git push private main

# Sync from public to private
git fetch origin && git merge origin/main && git push private main

# Sync from private to public (if safe)
git fetch private && git merge private/main && git push origin main
```

