# Tech Stack

## Core Technologies

### Python Scripts
Located in `scripts/`:
- `web_research.py` - Web search via Serper API
- `mem0_helpers.py` - Mem0 session management
- `analysis_tools.py` - TAM/SAM/SOM calculations
- `slack_helpers.py` - Slack notifications and formatting

### Key Libraries
- `mem0` - Session state management across agents
- `requests` - HTTP requests for Slack/Serper APIs
- `re` - Regex for markdown-to-Slack conversion

## Claude Code Configuration

### Agents
Located in `.claude/agents/`:
- `market-researcher.md` - Market analysis agent
- `customer-solution.md` - Customer discovery agent
- `feasibility-scorer.md` - Solution validation agent
- `report-pivot.md` - Report generation agent
- `deep-research-analyst.md` - High-quality research with confidence scoring

### Skills (Slash Commands)
Located in `.claude/commands/`:
- `/validate <problem>` - Full ideation pipeline
- `/quick-check <problem>` - Lightweight validation (market + customer only)
- `/compare <problem1> vs <problem2>` - Side-by-side comparison
- `/report <session_id>` - Retrieve or regenerate a report
- `/research <topic>` - Deep research with confidence scoring and evidence chains

### Settings
- `.claude/settings.json` - Project permissions (acceptEdits, allowed commands)
- `.claude/rules/` - Claude rules (this directory)

## Environment Variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `MEM0_API_KEY` | Yes | Mem0 cloud storage |
| `SERPER_API_KEY` | Yes | Web search |
| `SLACK_BOT_TOKEN` | Yes | Slack notifications |
| `SLACK_CHANNEL_ID` | Yes | Slack channel |

## Output

- Reports saved to `reports/{name}-{session_id}.md`
- Slack notifications sent via Block Kit + full report
