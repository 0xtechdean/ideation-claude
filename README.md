# Ideation-Claude

Multi-agent startup problem validator using Claude Code native sub-agents.

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/0xtechdean/ideation-claude.git
cd ideation-claude

# 2. Set up environment
cp .env.example .env
# Edit .env with your API keys (MEM0_API_KEY, SERPER_API_KEY, SLACK_BOT_TOKEN, SLACK_CHANNEL_ID)

# 3. Start Claude Code in the repo
claude

# 4. Ask Claude to validate a problem
> Validate the problem: "Legal research is too time-consuming for small law firms"
```

That's it! Claude reads `CLAUDE.md`, orchestrates 4 sub-agents, and delivers a comprehensive evaluation report.

## Features

- **Autonomous Execution**: Uses ralph-wiggum plugin for hands-free operation
- **Opus 4.5 Model**: All agents run on Claude's most capable model
- **Two-Phase Validation**: Problem validation must pass before solution validation
- **Early Elimination**: Skip solution phase if problem_score < 6.0
- **Parallel Agents**: Problem validation agents run simultaneously
- **Full Reports**: Saved to `reports/` and sent to Slack

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       Slack Trigger                             │
│    @Claude go to ideation-claude and validate "problem"         │
└─────────────────────────────┬───────────────────────────────────┘
                              │ triggers
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                 ORCHESTRATOR (Claude Code)                      │
│                                                                 │
│   Phase 1: PROBLEM VALIDATION (parallel)                       │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │  ┌──────────────┐  ┌──────────────┐                     │  │
│   │  │   market-    │  │  customer-   │                     │  │
│   │  │  researcher  │  │   solution   │                     │  │
│   │  └──────┬───────┘  └──────┬───────┘                     │  │
│   │         └────────┬────────┘                             │  │
│   │                  ▼                                      │  │
│   │         Calculate problem_score                         │  │
│   └─────────────────────────────────────────────────────────┘  │
│                              │                                  │
│           problem_score < 6.0? ──► ELIMINATE ──┐               │
│                              │                  │               │
│                              ▼ (if passes)      │               │
│   Phase 2: SOLUTION VALIDATION                  │               │
│   ┌──────────────────────────────────────────┐  │               │
│   │         ┌──────────────┐                 │  │               │
│   │         │ feasibility- │                 │  │               │
│   │         │    scorer    │                 │  │               │
│   │         └──────┬───────┘                 │  │               │
│   │                ▼                         │  │               │
│   │    combined = (problem×60%)+(solution×40%)  │               │
│   └──────────────────────────────────────────┘  │               │
│                              │                  │               │
│                              ◄──────────────────┘               │
│                              ▼                                  │
│   Phase 3: REPORT                                              │
│   ┌──────────────────────────────────────────────────────────┐ │
│   │              ┌──────────────────┐                        │ │
│   │              │   report-pivot   │ (+ pivots if failed)   │ │
│   │              └──────────────────┘                        │ │
│   └──────────────────────────────────────────────────────────┘ │
│                              │                                  │
│   Phase 4: Save report to reports/                             │
│   Phase 5: Send summary to Slack                               │
└─────────────────────────────────────────────────────────────────┘
```

## How It Works

1. User in Slack: `@Claude go to ideation-claude and validate "problem statement"`
2. Claude Code reads CLAUDE.md and manages the entire flow
3. **Phase 1: PROBLEM VALIDATION** (parallel):
   - `market-researcher` - Market trends, TAM/SAM/SOM, market size score
   - `customer-solution` - Customer segments, pain points, WTP score
   - Calculate `problem_score` (severity, market, WTP, solution fit)
4. **DECISION POINT**: If `problem_score < 6.0` → ELIMINATE → Skip to Phase 3
5. **Phase 2: SOLUTION VALIDATION** (only if problem passes):
   - `feasibility-scorer` - Competition, tech stack, resource requirements
   - Calculate `solution_score` and `combined_score`
6. **Phase 3**: `report-pivot` compiles final report (+ pivot suggestions if failed)
7. **Phase 4**: Saves report to `reports/{problem}-evaluation-{session_id}.md`
8. **Phase 5**: Sends summary to Slack

## Native Sub-Agents

All agents are defined in `.claude/agents/` as markdown files:

| Agent | File | Role |
|-------|------|------|
| Market Researcher | `market-researcher.md` | Market trends, pain points, TAM/SAM/SOM |
| Customer Solution | `customer-solution.md` | Customer segments, MVP design, pricing |
| Feasibility Scorer | `feasibility-scorer.md` | Competition, tech stack, 8-criteria scoring |
| Report & Pivot | `report-pivot.md` | Final report compilation, pivot suggestions |

## Evaluation Pipeline

```
PHASE 1: PROBLEM VALIDATION (parallel)
├── market-researcher  ─┐
└── customer-solution  ─┴──► Calculate problem_score
         │
         ▼
    problem_score < 6.0?
         │
    ┌────┴────┐
    │  YES    │──► ELIMINATE ──► report-pivot ──► Report + Pivot Suggestions
    └────┬────┘
         │ NO
         ▼
PHASE 2: SOLUTION VALIDATION
└── feasibility-scorer ──► Calculate solution_score
         │
         ▼
    combined = (problem × 60%) + (solution × 40%)
         │
         ▼
    combined >= 6.0? ──► PASS ──► report-pivot ──► Final Report
         │
    combined < 6.0?  ──► FAIL ──► report-pivot ──► Report + Pivot Suggestions
```

## Scoring Criteria

### Problem Validation (60% weight)
| Criteria | Weight |
|----------|--------|
| Problem Severity | 25% |
| Market Size | 25% |
| Willingness to Pay | 25% |
| Solution Fit | 25% |

### Solution Validation (40% weight)
| Criteria |
|----------|
| Technical Viability |
| Competitive Advantage |
| Resource Requirements |
| Time to Market |

**Passing Threshold**: Combined score >= 6.0/10

## Usage

### Option 1: Direct with Claude Code (Recommended)
```bash
# Clone and start
git clone https://github.com/0xtechdean/ideation-claude.git
cd ideation-claude
claude

# Then ask Claude:
> Validate the problem: "Your problem statement here"

# Or use ralph-wiggum for fully autonomous execution:
> /ralph-loop "Validate the problem: Your problem statement here" --max-iterations 30
```

### Option 2: Via Slack
```bash
@Claude go to https://github.com/0xtechdean/ideation-claude and validate "Your problem statement here"
```

## Performance

| Metric | Time |
|--------|------|
| Phase 1: Problem Validation | ~4-5 min |
| Phase 2: Solution Validation | ~3-4 min |
| Phase 3: Report Generation | ~2-3 min |
| **Full Flow (passes)** | **~10-12 min** |
| **Early Elimination** | **~5-7 min** |

## Helper Scripts

Located in `scripts/`:

| Script | Purpose |
|--------|---------|
| `web_research.py` | Web search via Serper API |
| `mem0_helpers.py` | Mem0 session management |
| `analysis_tools.py` | TAM/SAM calculations |
| `slack_helpers.py` | Slack notification formatting |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `MEM0_API_KEY` | Yes | Mem0 cloud storage |
| `SERPER_API_KEY` | Yes | Web search via Serper |
| `SLACK_BOT_TOKEN` | Yes | Slack Bot Token (xoxb-...) |
| `SLACK_CHANNEL_ID` | Yes | Channel for notifications |

## Project Structure

```
ideation-claude/
├── CLAUDE.md                    # Orchestrator instructions
├── .claude/
│   ├── settings.json            # Claude Code config (acceptEdits)
│   └── agents/
│       ├── market-researcher.md
│       ├── customer-solution.md
│       ├── feasibility-scorer.md
│       └── report-pivot.md
├── scripts/
│   ├── web_research.py
│   ├── mem0_helpers.py
│   ├── analysis_tools.py
│   └── slack_helpers.py
├── reports/                     # Generated evaluation reports
└── .env.example
```

## License

MIT
