# Private Repository Setup Guide

This guide helps you fork the repository to a private repo, add your `.env` secrets, and run GitHub Actions.

## Step 1: Fork to Private Repository

### Option A: Using GitHub Web Interface

1. Go to: https://github.com/0xtechdean/ideation-claude
2. Click **"Fork"** button (top right)
3. In the fork dialog:
   - Change owner to your account
   - **Important**: Check **"Copy the main branch only"**
   - Click **"Create fork"**
4. After forking, go to your fork's **Settings** → **General**
5. Scroll down to **"Danger Zone"**
6. Click **"Change visibility"** → **"Make private"**
7. Confirm the change

### Option B: Using GitHub CLI

```bash
# Install GitHub CLI if needed: brew install gh

# Authenticate
gh auth login

# Fork the repository
gh repo fork 0xtechdean/ideation-claude --clone

# Navigate to the forked repo
cd ideation-claude

# Make it private
gh repo edit --visibility private
```

## Step 2: Add Secrets to GitHub

### Using GitHub Web Interface

1. Go to your **private fork** on GitHub
2. Navigate to: **Settings** → **Secrets and variables** → **Actions**
3. Click **"New repository secret"** for each variable:

#### Required Secrets:

**ANTHROPIC_API_KEY**
- Name: `ANTHROPIC_API_KEY`
- Value: (from your `.env` file)
- Click **"Add secret"**

**MEM0_API_KEY** (Optional)
- Name: `MEM0_API_KEY`
- Value: (from your `.env` file, or leave empty)
- Click **"Add secret"**

**OPENAI_API_KEY** (Optional)
- Name: `OPENAI_API_KEY`
- Value: (from your `.env` file, or leave empty)
- Click **"Add secret"**

### Using GitHub CLI

```bash
# Set secrets (replace with your actual values)
gh secret set ANTHROPIC_API_KEY --repo your-username/ideation-claude
gh secret set MEM0_API_KEY --repo your-username/ideation-claude
gh secret set OPENAI_API_KEY --repo your-username/ideation-claude

# Verify secrets are set
gh secret list --repo your-username/ideation-claude
```

## Step 3: Update Remote (if you cloned locally)

If you want to work with the private fork locally:

```bash
# Check current remote
git remote -v

# Update to point to your private fork
git remote set-url origin https://github.com/YOUR-USERNAME/ideation-claude.git

# Or add as new remote
git remote add private https://github.com/YOUR-USERNAME/ideation-claude.git
```

## Step 4: Trigger GitHub Actions Workflow

### Option A: Manual Trigger

1. Go to your private fork on GitHub
2. Click **"Actions"** tab
3. Select **"Tests"** workflow from the left sidebar
4. Click **"Run workflow"** button (top right)
5. Select branch: `main`
6. Click **"Run workflow"**

### Option B: Push a Commit

```bash
# Make a small change to trigger workflow
echo "# Test trigger" >> .github/workflows/.test-trigger
git add .github/workflows/.test-trigger
git commit -m "Trigger workflow test"
git push origin main
```

### Option C: Test the Ideation Workflow

1. Go to **Actions** → **Ideation Claude Evaluation**
2. Click **"Run workflow"**
3. Fill in the inputs:
   - **idea**: "AI-powered personal finance assistant"
   - **threshold**: 5.0
   - **subagent**: false (or true)
   - **quiet**: false
4. Click **"Run workflow"**

## Step 5: Monitor Workflow Execution

1. Go to **Actions** tab
2. Click on the running workflow
3. Watch the progress in real-time
4. Check logs for each step
5. Download artifacts (reports, coverage) when complete

## Security Notes

✅ **Private Repository**: Your secrets are safe in a private repo
✅ **Secrets are Encrypted**: GitHub encrypts all secrets at rest
✅ **No Log Exposure**: Secrets are masked in workflow logs
✅ **Access Control**: Only you (and collaborators) can see the repo

## Troubleshooting

### Secrets Not Working
- Verify secret names match exactly (case-sensitive)
- Check that secrets are set in the correct repository
- Ensure workflow uses `${{ secrets.SECRET_NAME }}` syntax

### Workflow Not Triggering
- Check that workflow file is in `.github/workflows/`
- Verify branch name matches workflow trigger
- Check Actions tab for any error messages

### Permission Errors
- Ensure you have admin access to the private repo
- Check repository settings allow Actions

## Next Steps

Once setup is complete:
1. ✅ Private repo created
2. ✅ Secrets added
3. ✅ Workflow triggered
4. ✅ Monitor execution
5. ✅ Download results

Your evaluations will run privately with your API keys securely stored!

