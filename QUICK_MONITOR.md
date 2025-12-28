# Quick Monitoring Reference

## 🚀 Quick Commands

### View Latest Workflow Status
```bash
gh run list --repo Othentic-Ai/ideation-claude --limit 5
```

### Watch Running Workflow
```bash
RUN_ID=$(gh run list --repo Othentic-Ai/ideation-claude --limit 1 --json databaseId --jq '.[0].databaseId')
gh run watch $RUN_ID --repo Othentic-Ai/ideation-claude
```

### View Logs
```bash
RUN_ID=$(gh run list --repo Othentic-Ai/ideation-claude --limit 1 --json databaseId --jq '.[0].databaseId')
gh run view $RUN_ID --repo Othentic-Ai/ideation-claude --log
```

### Use Monitor Script
```bash
./monitor-workflow.sh Othentic-Ai/ideation-claude ideation.yml
```

## 📊 Web Interface

**View All Workflows:**
https://github.com/Othentic-Ai/ideation-claude/actions

**View Latest Run:**
```bash
gh run view --repo Othentic-Ai/ideation-claude --web
```

## 🔍 Log Groups

The workflow uses GitHub Actions log groups for better organization:
- `🚀 Starting Evaluation` - Initial setup
- `📝 Reading ideas` - Input processing
- `💡 Evaluating Idea` - Individual idea evaluation
- `📊 Evaluation Summary` - Final statistics
- `📋 Workflow Summary` - Complete summary

## 📥 Download Artifacts

```bash
RUN_ID=$(gh run list --repo Othentic-Ai/ideation-claude --limit 1 --json databaseId --jq '.[0].databaseId')
gh run download $RUN_ID --repo Othentic-Ai/ideation-claude --dir artifacts
```

## 🎯 Status Indicators

- ✅ **Success**: Workflow completed successfully
- ❌ **Failure**: Workflow failed (check logs)
- 🟡 **In Progress**: Currently running
- ⏸️ **Queued**: Waiting to start

## 📈 Metrics

Metrics are automatically generated when using `--metrics` flag:
- Location: `metrics/*.json` (in artifacts)
- Contains: Phase timings, API calls, token usage
- Format: JSON for easy parsing

## 🔔 Notifications

Enable GitHub notifications:
1. Go to repository Settings → Notifications
2. Enable workflow run notifications
3. Choose your preferred method

