---
description: Compare two startup problem statements side-by-side
---

# Compare Problem Statements

Compare two startup problems to help decide which to pursue.

**Arguments:** $ARGUMENTS

## Instructions

Parse the arguments to extract two problems. Expected formats:
- `/compare "Problem A" vs "Problem B"`
- `/compare session_id1 session_id2` (compare existing reports)

### For New Problems:

1. **Run Quick Checks in Parallel**
   - Perform quick market research on both problems simultaneously
   - Score each on: severity, market size, willingness to pay

2. **Comparative Analysis**
   - Market opportunity comparison
   - Competition landscape comparison
   - Technical feasibility comparison
   - Time to market comparison

3. **Output Comparison Table**
   ```
   ## Problem Comparison

   | Criteria | Problem A | Problem B | Winner |
   |----------|-----------|-----------|--------|
   | Problem Severity | X/10 | Y/10 | A/B |
   | Market Size | X/10 | Y/10 | A/B |
   | Willingness to Pay | X/10 | Y/10 | A/B |
   | Competition | X/10 | Y/10 | A/B |
   | Feasibility | X/10 | Y/10 | A/B |
   | **Overall** | X/10 | Y/10 | **A/B** |

   ### Recommendation
   [Which problem to pursue and why]

   ### Key Differentiators
   - Problem A strengths: ...
   - Problem B strengths: ...

   ### Suggested Action
   - Run `/validate "winning problem"` for full analysis
   ```

### For Existing Sessions:

1. Load both reports from `reports/` directory
2. Extract scores and findings
3. Generate comparison table as above
4. Highlight which passed/failed and why

Keep analysis concise - this is for decision-making, not deep research.
