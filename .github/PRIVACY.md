# Privacy Guide for Public Repositories

## The Problem

If your repository is **public**, GitHub Actions workflow runs are visible to everyone. This means:

- ✅ **API keys are safe** - Secrets are masked and never exposed
- ❌ **Your ideas are visible** - Workflow inputs appear in the Actions tab
- ❌ **Results are visible** - Evaluation logs and outputs are public
- ❌ **Artifacts may be visible** - Report files can be downloaded by anyone

## Solutions

### Option 1: Use Private Workflow File (Recommended)

Use `ideation-private.yml` which:
- Only supports manual triggers (no automatic runs)
- Auto-deletes artifacts after 1 day
- Still visible but less likely to be discovered

**To use:**
1. Delete or rename `ideation.yml` 
2. Rename `ideation-private.yml` to `ideation.yml`
3. Or keep both and use the private one for sensitive evaluations

### Option 2: Exclude Workflow from Public Repo

If you want to keep workflows completely private:

1. **Add to `.gitignore`** (not recommended - breaks CI/CD):
   ```
   .github/workflows/ideation*.yml
   ```

2. **Better: Use a separate private branch**:
   ```bash
   # Create a private branch with workflows
   git checkout -b private-workflows
   # Add your workflow files
   git push origin private-workflows
   # Never merge to main
   ```

3. **Best: Use a private repository**:
   - Fork this repo to a private repository
   - Add your workflows there
   - Keep public repo for code sharing only

### Option 3: Run Locally

For maximum privacy, run evaluations locally:

```bash
# Install and run locally
pip install -e .
ideation-claude "Your sensitive idea"
```

No GitHub Actions = No public visibility.

### Option 4: GitHub Pro/Team

If you have GitHub Pro or Team:
- Check if your plan supports private workflows
- This feature may allow hiding workflow runs in public repos

## Recommendation

For a **public repository** with sensitive startup ideas:

1. **Don't use GitHub Actions** - Run evaluations locally
2. **OR** use a **private repository** for evaluations
3. **OR** accept that ideas will be visible (if not sensitive)

For a **private repository**:
- Use either workflow file - both are safe
- Workflow runs are only visible to repository collaborators

## Security Notes

- ✅ **Secrets are always safe** - GitHub Secrets are masked in logs
- ✅ **API keys won't leak** - Even if logs are public
- ❌ **Your ideas will be visible** - If you use workflows in public repos
- ❌ **Results will be visible** - Evaluation outputs appear in logs

