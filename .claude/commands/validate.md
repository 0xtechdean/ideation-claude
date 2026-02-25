---
description: Run the full ideation pipeline to validate a startup problem
---

# Validate Startup Problem

You are running the full ideation validation pipeline for the following problem:

**Problem:** $ARGUMENTS

## Instructions

Follow the complete orchestration flow from CLAUDE.md:

1. **Initialize Session**
   - Generate a unique 8-character session_id
   - Detect integrations: check `MEM0_API_KEY`, `SLACK_BOT_TOKEN`, `SLACK_CHANNEL_ID`
   - If `MEM0_API_KEY` is set: initialize Mem0 with session metadata
   - Set flags: `use_mem0` and `use_slack` for downstream agents

2. **Phase 1: Problem Validation** (PARALLEL)
   - Launch `market-researcher` agent - Market trends, TAM/SAM/SOM
   - Launch `customer-solution` agent - Customer segments, MVP design
   - Include in each Task prompt: `Mem0 persistence: enabled/disabled`
   - Calculate problem_score from agent output

3. **Decision Point**
   - If problem_score < 6.0 → ELIMINATE → Skip to Phase 3
   - If problem_score >= 6.0 → Continue to Phase 2

4. **Phase 2: Solution Validation** (only if problem passes)
   - Launch `feasibility-scorer` agent
   - Include in Task prompt: `Mem0 persistence: enabled/disabled`
   - Calculate combined_score = (problem × 60%) + (solution × 40%)

5. **Phase 3: Report**
   - Launch `report-pivot` agent
   - Generate comprehensive report with pivot suggestions if failed

6. **Phase 4: Save Report**
   - Save to `reports/{sanitized-name}-{session_id}.md`

7. **Phase 5: Notify** (if Slack configured)
   - If `SLACK_BOT_TOKEN` and `SLACK_CHANNEL_ID` are set:
     - Send Block Kit summary to Slack
     - Send full report to Slack (converted to mrkdwn)
   - If not set: skip, report is saved to disk

8. **Present Results**
   - Display summary table with scores and verdict
   - Provide file path to full report
   - List key findings and next steps

Use `model: opus` for all agents. Complete all phases before presenting results.
