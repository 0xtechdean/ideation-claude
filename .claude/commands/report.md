---
description: Retrieve or regenerate a session report by ID
---

# Report Retrieval

Retrieve or work with a session report.

**Arguments:** $ARGUMENTS

## Instructions

Parse the arguments to determine the action:

### If session_id provided (e.g., `/report abc12345`):
1. Look for existing report in `reports/` directory matching the session_id
2. If found:
   - Display the report contents
   - Offer options: "regenerate", "summarize"
   - If `SLACK_BOT_TOKEN` is set: also offer "resend to Slack"
3. If not found:
   - If `MEM0_API_KEY` is set: check Mem0 for session data with that ID
     - If session exists in Mem0, offer to regenerate the report
   - If `MEM0_API_KEY` is not set or no session found:
     - Inform user: "No report found for session {id}. Reports are available from `reports/` directory."

### If "list" or "all" provided (e.g., `/report list`):
1. List all reports in the `reports/` directory
2. Show: filename, date modified, verdict (if parseable from filename)
3. Format as table

### If "latest" provided (e.g., `/report latest`):
1. Find the most recently modified report in `reports/`
2. Display its contents

### If "resend {session_id}" provided:
1. Find the report file
2. If `SLACK_BOT_TOKEN` is set: resend to Slack using `send_full_report()`
3. If not set: inform user "Slack is not configured. Set SLACK_BOT_TOKEN and SLACK_CHANNEL_ID to enable."

## Output Format

For report display:
```
## Report: {session_id}

**File:** reports/{filename}.md
**Created:** {date}
**Verdict:** {PASS/FAIL}
**Score:** {X/10}

[Full report contents or summary based on length]
```

For listing:
```
## Available Reports

| Session | Problem | Score | Verdict | Date |
|---------|---------|-------|---------|------|
| abc123 | Legal research... | 7.5 | PASS | 2024-01-15 |
```
