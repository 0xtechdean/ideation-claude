# Ideation Flow Rules

## Execution Requirements

1. **Always use Opus 4.5** (`model: opus`) for all agents and tasks
2. **Use ralph-wiggum** for autonomous execution: `/ralph-loop "Validate: {problem}" --max-iterations 30`
3. **Never stop mid-flow** - complete all phases before presenting results
4. **Detect integrations early** - Run `python3 scripts/detect_integrations.py` at session init (reads from shell env AND `.env` file). Parse JSON output for `use_mem0` and `use_slack`. Pass `Mem0 persistence: enabled/disabled` flag in Task prompts to agents.

## Research Source Requirements

**ALWAYS prioritize non-promotional sources.** Extract and include relevant quotes.

### Preferred Sources (Use These)
| Source Type | Examples | Why |
|-------------|----------|-----|
| Research Reports | MIT, Gartner, Forrester, McKinsey | Data-driven, credible |
| Industry Publications | HBR, TechCrunch, VentureBeat | Editorial, fact-checked |
| Academic Papers | arxiv, ACM, IEEE | Peer-reviewed |
| Government/NGO | EU, NIST, CSA, OWASP | Authoritative |
| News Outlets | Reuters, Bloomberg, WSJ | Journalistic standards |

### Avoid These Sources
| Source Type | Examples | Why |
|-------------|----------|-----|
| Vendor Blogs | Company marketing blogs | Promotional bias |
| Product Pages | Pricing/features pages | Sales material |
| Press Releases | Company announcements | Self-serving |
| Sponsored Content | "Partnered with" articles | Paid placement |

### Quote Extraction Rules
- Extract 2-4 key quotes per major section
- Format: `> "Quote text" — Source Name, Date`
- Focus on statistics, pain points, and market insights
- Verify quotes match the actual article content

## Phase Execution Order

1. **Initialize**: Generate session_id, write to Mem0 (if `MEM0_API_KEY` configured)
2. **Phase 1**: Launch market-researcher + customer-solution IN PARALLEL
3. **Decision**: If problem_score < 6.0 → ELIMINATE → Skip to Phase 3
4. **Phase 2**: Launch feasibility-scorer (only if problem passes)
5. **Phase 3**: Launch report-pivot
6. **Phase 4**: Save report to `reports/{name}-{session_id}.md`
7. **Phase 5**: Send summary + full report to Slack (if `SLACK_BOT_TOKEN` configured)

## Scoring Rules

- **Problem Score** = (severity + market_size + wtp + solution_fit) / 4
- **Solution Score** = (tech_viability + competitive_advantage + resources + time_to_market) / 4
- **Combined Score** = (problem × 60%) + (solution × 40%)
- **Pass Threshold**: >= 6.0/10

## Agent Usage

Use the Task tool with these agent types:
- `market-researcher` - Market trends, TAM/SAM/SOM
- `customer-solution` - Customer segments, MVP design
- `feasibility-scorer` - Competition, tech feasibility
- `report-pivot` - Final report generation

## Slack Notifications

If `SLACK_BOT_TOKEN` and `SLACK_CHANNEL_ID` are set, send BOTH:
1. Block Kit summary via `send_evaluation_report()`
2. Full report via `send_full_report()` (converts markdown to Slack mrkdwn)

If Slack is not configured, skip Phase 5. Report is saved to disk in Phase 4.
