---
description: Quick lightweight validation of a startup idea (market + customer only)
---

# Quick Problem Check

Perform a lightweight validation of the following problem:

**Problem:** $ARGUMENTS

## Instructions

This is a quick check - only run Phase 1 (Problem Validation) without full pipeline.

1. **Initialize**
   - Generate session_id
   - Note this is a "quick-check" session

2. **Market Research** (via web search)
   - Identify 3-5 key market trends
   - Estimate rough TAM (use available data)
   - Find 2-3 existing solutions/competitors

3. **Customer Analysis**
   - Identify 2-3 potential customer segments
   - Assess problem severity (1-10)
   - Estimate willingness to pay (1-10)

4. **Quick Score**
   - Calculate quick_score = (severity + market_potential + wtp) / 3
   - Provide go/no-go recommendation

5. **Output**
   Present a concise summary:
   ```
   ## Quick Check Results

   | Metric | Score |
   |--------|-------|
   | Problem Severity | X/10 |
   | Market Potential | X/10 |
   | Willingness to Pay | X/10 |
   | **Quick Score** | X/10 |

   **Recommendation:** [GO / NEEDS MORE RESEARCH / NO-GO]

   ### Key Findings
   - Finding 1
   - Finding 2
   - Finding 3

   ### Suggested Next Steps
   - If GO: Run `/validate` for full analysis
   - If uncertain: [specific research needed]
   ```

Do NOT run the full pipeline. This is meant to be fast (~2-3 minutes).
