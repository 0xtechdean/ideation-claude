# Quick Start: Private Repository Setup

## Fast Setup (5 minutes)

### 1. Fork to Private (2 min)

```bash
# Using GitHub CLI (recommended)
gh repo fork 0xtechdean/ideation-claude --clone
cd ideation-claude
gh repo edit --visibility private

# Or use web interface:
# 1. Fork at: https://github.com/0xtechdean/ideation-claude
# 2. Settings → General → Danger Zone → Make private
```

### 2. Add Secrets (2 min)

**Using GitHub CLI:**
```bash
# From your .env file
gh secret set ANTHROPIC_API_KEY --repo YOUR-USERNAME/ideation-claude < .env
gh secret set MEM0_API_KEY --repo YOUR-USERNAME/ideation-claude < .env  
gh secret set OPENAI_API_KEY --repo YOUR-USERNAME/ideation-claude < .env
```

**Or manually:**
1. Go to: `https://github.com/YOUR-USERNAME/ideation-claude/settings/secrets/actions`
2. Add each secret from your `.env` file

### 3. Run Workflow (1 min)

1. Go to: `https://github.com/YOUR-USERNAME/ideation-claude/actions`
2. Click **"Ideation Claude Evaluation"**
3. Click **"Run workflow"**
4. Enter idea: `"AI-powered personal finance assistant"`
5. Click **"Run workflow"**

## Using the Helper Script

```bash
./setup-private-repo.sh
```

This interactive script will guide you through the entire process.

## Verify Secrets

```bash
gh secret list --repo YOUR-USERNAME/ideation-claude
```

Should show:
- ✅ ANTHROPIC_API_KEY
- ✅ MEM0_API_KEY (if set)
- ✅ OPENAI_API_KEY (if set)

## Test the Workflow

Once secrets are set, workflows will automatically use them. No need to modify workflow files!

## Security Checklist

- ✅ Repository is private
- ✅ Secrets are added (not committed)
- ✅ `.env` is in `.gitignore`
- ✅ Workflow runs in private repo only

