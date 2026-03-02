---
description: Discover startup problems by mining 5 data sources for authentic user pain signals
---

# Discover Problems: $ARGUMENTS

Run the Phase 0 Discovery Pipeline to find startup problems worth validating.

## Instructions

Mine authentic user pain from 5 data sources, cluster signals into problem themes, and rank them by signal strength.

**Market Vertical / Search Focus:** $ARGUMENTS

If the argument is "broad", search across all verticals. Otherwise, use it as the market vertical (e.g., "devtools", "fintech", "healthcare", "ai_ml", "enterprise", "saas", "legal", "ecommerce", "education").

If the argument doesn't match a predefined vertical key, treat it as a free-text topic and search across the "broad" subreddit set plus topic-specific queries.

## Execution Steps

1. **Generate session_id** (8 random alphanumeric chars)

2. **Initialize Mem0** — Write session start with discovery type

3. **Launch discovery-engine agent** with:
   - Market vertical from $ARGUMENTS
   - Session ID
   - The agent will:
     a. Run `run_discovery_sweep()` across all 5 sources
     b. Deep-read top 15-20 signals via WebFetch
     c. Cluster into 10-20 problem themes
     d. Rank by signal strength (frequency 30%, engagement 20%, recency 20%, specificity 15%, regulatory 15%)
     e. Classify each theme by software executability (Pure SW / SW-First / SW+Svc / Ops-Heavy)
     f. Assess defensibility moat for each theme — flag "Moat Risk" if the only moat is the software itself (AI can rebuild any pure CRUD/workflow tool in weeks)
     g. Deprioritize Ops-Heavy and Moat Risk themes — reorder so defensible software problems rank highest
     h. Write to Mem0

4. **Save discovery report** to `discoveries/{vertical}-{session_id}.md`

5. **Send summary to Slack** — Use `send_simple_notification()` from `scripts/slack_helpers.py`:
   - Title: "Discovery Complete: {vertical}"
   - Body: Top 5 problems with signal strength scores

6. **Present results to user:**
   - Show top 5 problem themes with scores
   - Provide ready-to-use `/quick-check` prompts
   - Show file path to full report

## Output Format

```
## Discovery Complete — Session {session_id}

**Vertical:** {vertical}
**Signals Mined:** {N} from 5 sources
**Problem Themes:** {N} identified

### Top 5 Discovered Problems

| Rank | Problem | Signal | SW Class | Moat | Signals |
|------|---------|--------|----------|------|---------|
| 1 | {problem} | X.X/10 | Pure SW | Data NE | N |
| 2 | {problem} | X.X/10 | SW-First | Reg Lock-in | N |
| 3 | {problem} | X.X/10 | Pure SW | Domain Data | N |
| 4 | {problem} | X.X/10 | SW+Svc | Integration | N |
| 5 | {problem} | X.X/10 | Pure SW | Brand/Trust | N |

### Ready to Validate

1. `/quick-check "{problem 1}"`
2. `/quick-check "{problem 2}"`
3. `/quick-check "{problem 3}"`
4. `/quick-check "{problem 4}"`
5. `/quick-check "{problem 5}"`

Full report: `discoveries/{vertical}-{session_id}.md`
```
