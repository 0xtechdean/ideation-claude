# Tech Stack

## Core Technologies

### Python Scripts
Located in `scripts/`:
- `web_research.py` - Web search via Serper API
- `discovery_sources.py` - 5-source discovery pipeline (Arctic Shift, PullPush, HN Algolia, Federal Register, Serper Reddit dorks)
- `mem0_helpers.py` - Mem0 session management (optional)
- `analysis_tools.py` - TAM/SAM/SOM calculations
- `slack_helpers.py` - Slack notifications and formatting (optional)

### Key Libraries
- `mem0` - Session persistence (optional - pipeline works without it)
- `requests` - HTTP requests for Slack/Serper APIs
- `re` - Regex for markdown-to-Slack conversion

## Claude Code Configuration

### Agents
Located in `.claude/agents/`:
- `discovery-engine.md` - Problem discovery from 5 data sources (Phase 0)
- `market-researcher.md` - Market analysis agent
- `customer-solution.md` - Customer discovery agent
- `feasibility-scorer.md` - Solution validation agent
- `report-pivot.md` - Report generation agent
- `deep-research-analyst.md` - High-quality research with confidence scoring

### Skills (Slash Commands)
Located in `.claude/commands/`:
- `/discover <vertical>` - Mine 5 sources for pain signals, discover problems (Phase 0)
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
| `SERPER_API_KEY` | Recommended | Web search |
| `MEM0_API_KEY` | Optional | Session persistence via Mem0 |
| `SLACK_BOT_TOKEN` | Optional | Slack notifications |
| `SLACK_CHANNEL_ID` | Optional | Slack channel |

## Output

- Discovery reports saved to `discoveries/{vertical}-{session_id}.md`
- Validation reports saved to `reports/{name}-{session_id}.md`
- Slack notifications sent via Block Kit + full report (if Slack configured)
