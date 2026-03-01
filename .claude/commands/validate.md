---
description: Run the full ideation pipeline to validate a startup problem
---

# Validate Startup Problem (v2.0)

You are running the full ideation validation pipeline for the following problem:

**Problem:** $ARGUMENTS

## Instructions

Follow the complete orchestration flow from CLAUDE.md (v2.0 scoring model):

1. **Initialize Session**
   - Generate a unique 8-character session_id
   - Initialize Mem0 with session metadata

2. **Phase 1: Problem Validation** (PARALLEL)
   - Launch `market-researcher` agent - Market trends, TAM/SAM/SOM, **Market Timing score (1-10)**
   - Launch `customer-solution` agent - Customer segments, MVP design, **WTP evidence tier (1/2/3)**
   - Cap WTP score based on evidence tier (Tier 3 max = 4)
   - Calculate problem_score from **5 criteria** (pain, addressability, market, WTP, timing)

3. **Decision Point (v2.0 — multiple elimination paths)**
   - If market_timing < 4 → EARLY ELIMINATION → Skip to Phase 3
   - If problem_score < 6.0 → ELIMINATE → Skip to Phase 3
   - If problem_score >= 6.0 → Continue to Phase 2

4. **Phase 2: Solution Validation** (only if problem passes)
   - Launch `feasibility-scorer` agent
   - **Kill switch gates run FIRST** (competitor $20M+, regulatory, timing)
   - Any kill switch triggered → AUTO-FAIL
   - Competitive Advantage ≤ 3 → AUTO-FAIL
   - Calculate combined_score = (problem × **55%**) + (solution × **45%**)
   - If combined 6.0-6.5: Run **smart mediocrity check** (3+ red flags = FAIL)

5. **Phase 3: Report**
   - Launch `report-pivot` agent
   - Report includes kill switch results, split severity, WTP tier, timing score
   - Generate comprehensive report with pivot suggestions if failed

6. **Phase 4: Save Report**
   - Save to `reports/{sanitized-name}-{session_id}.md`

7. **Phase 5: Notify**
   - Send Block Kit summary to Slack
   - Send full report to Slack (converted to mrkdwn)

8. **Present Results**
   - Display summary table with scores, kill switch results, and verdict
   - Provide file path to full report
   - List key findings and next steps

Use `model: opus` for all agents. Complete all phases before presenting results.
