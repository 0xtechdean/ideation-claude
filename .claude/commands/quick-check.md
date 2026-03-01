---
description: Quick lightweight validation of a startup idea (market + customer only)
---

# Quick Problem Check (v2.0)

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
   - **Assess Market Timing (1-10)** — is the market ready NOW?

3. **Customer Analysis**
   - Identify 2-3 potential customer segments
   - Assess problem severity (1-10)
   - Estimate willingness to pay (1-10)
   - **Classify WTP evidence tier** (Tier 1/2/3)

4. **Quick Kill Switch Scan**
   - Does a funded competitor ($20M+) already have the exact product?
   - Is the core feature legally prohibited?
   - Is the market at <2% penetration with no paying customers?

5. **Quick Score (v2.0)**
   - Calculate quick_score = (severity + market_potential + wtp_capped + market_timing) / 4
   - Check for kill switch triggers
   - Provide go/no-go recommendation

6. **Output**
   Present a concise summary:
   ```
   ## Quick Check Results (v2.0)

   ### Kill Switch Scan
   | Gate | Status |
   |------|--------|
   | Competitor ($20M+ exact product) | CLEAR / TRIGGERED |
   | Regulatory (prohibited) | CLEAR / TRIGGERED |
   | Timing (<2% penetration) | CLEAR / TRIGGERED |

   | Metric | Score | Notes |
   |--------|-------|-------|
   | Problem Severity | X/10 | |
   | Market Potential | X/10 | |
   | Willingness to Pay | X/10 | Tier X (capped from Y) |
   | Market Timing | X/10 | |
   | **Quick Score** | X/10 | |

   **Recommendation:** [GO / NEEDS MORE RESEARCH / NO-GO]

   ### Key Findings
   - Finding 1
   - Finding 2
   - Finding 3

   ### Suggested Next Steps
   - If GO: Run `/validate` for full analysis
   - If uncertain: [specific research needed]
   - If NO-GO: [why and what to look at instead]
   ```

Do NOT run the full pipeline. This is meant to be fast (~2-3 minutes).
