# Monitoring and Logs Guide

## Real-Time Monitoring

### Using GitHub CLI

**Watch a running workflow:**
```bash
# Get the latest run ID
RUN_ID=$(gh run list --repo Othentic-Ai/ideation-claude --limit 1 --json databaseId --jq '.[0].databaseId')

# Watch in real-time
gh run watch $RUN_ID --repo Othentic-Ai/ideation-claude
```

**View workflow status:**
```bash
# List recent runs
gh run list --repo Othentic-Ai/ideation-claude --limit 10

# View specific run details
gh run view <run-id> --repo Othentic-Ai/ideation-claude

# View logs
gh run view <run-id> --repo Othentic-Ai/ideation-claude --log

# View only failed steps
gh run view <run-id> --repo Othentic-Ai/ideation-claude --log-failed
```

**Using the monitor script:**
```bash
./monitor-workflow.sh Othentic-Ai/ideation-claude ideation.yml
```

### Using GitHub Web Interface

1. **View All Workflows:**
   https://github.com/Othentic-Ai/ideation-claude/actions

2. **View Specific Run:**
   - Click on any workflow run
   - See real-time logs
   - Download artifacts
   - View job details

3. **Filter and Search:**
   - Filter by workflow name
   - Filter by status (success, failure, in_progress)
   - Search by commit message

## Log Levels and Output

### Workflow Logs

The workflow provides detailed logging at each step:

1. **Setup Phase:**
   - Python version setup
   - Node.js setup
   - Claude CLI installation
   - Dependency installation

2. **Execution Phase:**
   - Phase-by-phase progress
   - Agent execution status
   - API call tracking
   - Error messages

3. **Completion Phase:**
   - Summary statistics
   - Report generation
   - Artifact upload

### Monitoring Metrics

When using `--metrics` flag, additional metrics are available:

**JSON Metrics File:**
- Location: `metrics/{topic}_metrics.json`
- Contains: Phase timings, API calls, token usage
- Available as workflow artifact

**Console Output:**
- Progress bars (with `rich`)
- Phase status updates
- Summary tables

## Monitoring Tools

### 1. GitHub Actions Dashboard

**URL:** https://github.com/Othentic-Ai/ideation-claude/actions

Features:
- Real-time status
- Log streaming
- Artifact downloads
- Run history
- Status badges

### 2. GitHub CLI Monitoring

```bash
# Continuous monitoring script
while true; do
  clear
  ./monitor-workflow.sh Othentic-Ai/ideation-claude
  sleep 30
done
```

### 3. Workflow Status API

```bash
# Get workflow status as JSON
gh api repos/Othentic-Ai/ideation-claude/actions/runs \
  --jq '.workflow_runs[] | {id: .id, status: .status, conclusion: .conclusion}'
```

## Log Analysis

### Common Log Patterns

**Success Indicators:**
- `✓ Phase completed`
- `Evaluation completed successfully`
- `Report saved to: reports/`

**Warning Indicators:**
- `⚠ Warning:`
- `Skipping phase`
- `Using fallback`

**Error Indicators:**
- `ERROR:`
- `Traceback:`
- `Failed:`
- `Exit code: 1`

### Filtering Logs

```bash
# View only errors
gh run view <run-id> --repo Othentic-Ai/ideation-claude --log | grep -i error

# View phase completions
gh run view <run-id> --repo Othentic-Ai/ideation-claude --log | grep "Phase"

# View API calls
gh run view <run-id> --repo Othentic-Ai/ideation-claude --log | grep "API"
```

## Alerts and Notifications

### GitHub Notifications

Enable notifications in repository settings:
1. Go to Settings → Notifications
2. Enable workflow run notifications
3. Choose notification preferences

### Status Badges

Add to README:
```markdown
![Workflow Status](https://github.com/Othentic-Ai/ideation-claude/actions/workflows/ideation.yml/badge.svg)
```

### Webhook Integration

Set up webhooks for:
- Workflow completion
- Workflow failures
- Status changes

## Metrics Dashboard

### Available Metrics

1. **Execution Metrics:**
   - Total duration
   - Phase durations
   - API call counts
   - Token usage

2. **Success Metrics:**
   - Pass rate
   - Average scores
   - Elimination rate

3. **Performance Metrics:**
   - Slowest phases
   - Bottlenecks
   - Resource usage

### Accessing Metrics

**From Workflow Artifacts:**
1. Go to workflow run
2. Download `evaluation-reports` artifact
3. Extract `metrics/*.json` files
4. Analyze with your tools

**Programmatic Access:**
```python
import json
from pathlib import Path

metrics_file = Path("metrics/idea_metrics.json")
metrics = json.loads(metrics_file.read_text())

print(f"Duration: {metrics['total_duration']}s")
print(f"API Calls: {metrics['total_api_calls']}")
print(f"Score: {metrics['final_score']}")
```

## Troubleshooting

### Workflow Not Starting

```bash
# Check workflow syntax
gh workflow view ideation.yml --repo Othentic-Ai/ideation-claude --yaml

# Check for errors
gh run list --repo Othentic-Ai/ideation-claude --limit 5
```

### Logs Not Appearing

- Wait a few seconds (logs stream in real-time)
- Check if workflow is actually running
- Verify repository permissions

### Performance Issues

- Check phase durations in metrics
- Look for slow API calls
- Review parallel execution logs

## Best Practices

1. **Monitor Regularly:**
   - Check workflow status daily
   - Review failed runs immediately
   - Track performance trends

2. **Set Up Alerts:**
   - Email notifications for failures
   - Slack/Discord webhooks
   - Status page integration

3. **Archive Metrics:**
   - Download metrics JSON files
   - Store in time-series database
   - Create dashboards

4. **Log Retention:**
   - GitHub keeps logs for 90 days
   - Download important runs
   - Archive locally if needed

