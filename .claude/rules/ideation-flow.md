# Ideation Flow Rules (v2.0)

## Execution Requirements

1. **Always use Opus** (`model: opus`) for all agents and tasks
2. **Use ralph-wiggum** for autonomous execution: `/ralph-loop "Validate: {problem}" --max-iterations 30`
3. **Never stop mid-flow** - complete all phases before presenting results
4. **Detect integrations early** - Run `python3 scripts/detect_integrations.py` at session init (reads from shell env AND `.env` file). Parse JSON output for `use_mem0` and `use_slack`. Pass `Mem0 persistence: enabled/disabled` flag in Task prompts to agents.

## v2.0 Changes Summary

The scoring model was overhauled after analyzing 130 reports. Key changes:
- **Kill switch gates** that auto-fail regardless of scores
- **Split Problem Severity** into Pain Severity + Startup Addressability
- **Market Timing** as standalone criterion (< 4 = early elimination)
- **WTP evidence tiers** that cap the maximum WTP score
- **Competitive Advantage floor** (≤ 3 = auto-fail)
- **Smart mediocrity check** for marginal passes (6.0-6.5)
- **55/45 weighting** (up from 60/40 for solution weight)

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
3. **Decision**:
   - If market_timing < 4 → EARLY ELIMINATION
   - If problem_score < 6.0 → ELIMINATE → Skip to Phase 3
4. **Phase 2**: Launch feasibility-scorer (only if problem passes)
   - Kill switch gates run FIRST
   - CA floor check (≤ 3 = auto-fail)
   - Smart mediocrity check if combined 6.0-6.5
5. **Phase 3**: Launch report-pivot
6. **Phase 4**: Save report to `reports/{name}-{session_id}.md`
7. **Phase 5**: Send summary + full report to Slack (if `SLACK_BOT_TOKEN` configured)

## Scoring Rules (v2.0)

### Problem Score (5 criteria, equal 20% weight)
```
problem_score = (pain_severity + startup_addressability + market_size + wtp_capped + market_timing) / 5
```

### WTP Capping
- **Tier 1** (direct payments): max 10
- **Tier 2** (validated pricing): max 7
- **Tier 3** (adjacent spending only): max 4

### Solution Score
```
solution_score = (tech_viability + competitive_advantage + resources + time_to_market) / 4
```

### Combined Score
```
combined = (problem × 55%) + (solution × 45%)
```

### Kill Switches (any = AUTO-FAIL)
- Funded competitor ($20M+) has exact product
- Core feature legally prohibited or $500K+/12mo+ licensing
- Market <2% penetration with no paying customers today

### Auto-Fail Conditions
- Any kill switch triggered
- Competitive Advantage ≤ 3
- Market Timing < 4 (early elimination)
- Smart mediocrity check fails (3+ red flags in 6.0-6.5 zone)

### Pass Threshold
- Combined >= 6.5: PASS
- Combined 6.0-6.5: Smart mediocrity check required
- Combined < 6.0: FAIL

## Agent Usage

Use the Agent tool with these agent types:
- `market-researcher` - Market trends, TAM/SAM/SOM, **Market Timing score**
- `customer-solution` - Customer segments, MVP design, **WTP evidence tier**
- `feasibility-scorer` - **Kill switches**, competition, tech feasibility, **CA floor check**
- `report-pivot` - Final report generation with **kill switch results and v2.0 scoring**

## Slack Notifications

If `SLACK_BOT_TOKEN` and `SLACK_CHANNEL_ID` are set, send BOTH:
1. Block Kit summary via `send_evaluation_report()`
2. Full report via `send_full_report()` (converts markdown to Slack mrkdwn)

If Slack is not configured, skip Phase 5. Report is saved to disk in Phase 4.
