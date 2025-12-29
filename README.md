# Ideation-Claude

Multi-agent startup problem validator using Claude Code.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Cursor Slack App                             │
│              /ideation evaluate "problem"                        │
└─────────────────────────────┬───────────────────────────────────┘
                              │ webhook + repo URL
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      claude.ai/code                              │
│  Opens repo URL → Reads CLAUDE.md → Executes agent logic         │
│  (Runs sequentially: researcher → market-analyst → ... )        │
└─────────────────────────────┬───────────────────────────────────┘
                              │ read/write
                              ▼
                    ┌───────────────────┐
                    │       Mem0        │
                    │  (Shared Context) │
                    └───────────────────┘
```

## How It Works

1. User in Slack: `/ideation evaluate "Legal research is too expensive"`
2. Cursor Slack App receives the command
3. Slack App triggers [claude.ai/code](https://claude.ai/code) with:
   - Repo URL: `github.com/Othentic-Ai/ideation-agent-researcher`
   - Prompt: session_id + problem statement
4. claude.ai/code opens the repo, reads `CLAUDE.md`, executes
5. Agent writes results to Mem0 under session_id
6. Slack App triggers next agent (market-analyst)
7. Repeat for all 9 agents
8. Final report posted back to Slack

## Agent Repositories

Each agent is a minimal repo with just `CLAUDE.md` + `README.md`:

| Agent | Repository | Role |
|-------|------------|------|
| Researcher | [ideation-agent-researcher](https://github.com/Othentic-Ai/ideation-agent-researcher) | Market trends & pain points |
| Market Analyst | [ideation-agent-market-analyst](https://github.com/Othentic-Ai/ideation-agent-market-analyst) | TAM/SAM/SOM calculations |
| Customer Discovery | [ideation-agent-customer-discovery](https://github.com/Othentic-Ai/ideation-agent-customer-discovery) | Mom Test interview framework |
| Scoring Evaluator | [ideation-agent-scoring-evaluator](https://github.com/Othentic-Ai/ideation-agent-scoring-evaluator) | 8-criteria opportunity scoring |
| Competitor Analyst | [ideation-agent-competitor-analyst](https://github.com/Othentic-Ai/ideation-agent-competitor-analyst) | Competitive landscape analysis |
| Resource Scout | [ideation-agent-resource-scout](https://github.com/Othentic-Ai/ideation-agent-resource-scout) | Technical feasibility & resources |
| Hypothesis Architect | [ideation-agent-hypothesis-architect](https://github.com/Othentic-Ai/ideation-agent-hypothesis-architect) | Lean Startup framework & MVP |
| Pivot Advisor | [ideation-agent-pivot-advisor](https://github.com/Othentic-Ai/ideation-agent-pivot-advisor) | Strategic alternatives |
| Report Generator | [ideation-agent-report-generator](https://github.com/Othentic-Ai/ideation-agent-report-generator) | Final evaluation report |

### Agent Repo Structure

```
ideation-agent-{name}/
├── CLAUDE.md        # Agent instructions (Claude Code reads this)
└── README.md        # Documentation
```

No Python packages, no GitHub Actions - just instructions for Claude Code.

## Evaluation Pipeline

```
PROBLEM VALIDATION PHASE
├── 1. Researcher Agent (trends & pain points)
├── 2. Market Analyst Agent (TAM/SAM/SOM)
├── 3. Customer Discovery Agent (Mom Test)
└── 4. Scoring Evaluator Agent (problem score)
        │
        ├── Score < Threshold? → ELIMINATE → Pivot Advisor → Report
        │
        └── Score ≥ Threshold? → Continue ↓

SOLUTION VALIDATION PHASE
├── 5. Competitor Analyst Agent (landscape)
├── 6. Resource Scout Agent (feasibility)
├── 7. Hypothesis Architect Agent (MVP)
└── 8. Scoring Evaluator Agent (solution score)
        │
        └── Combined Score (60% problem + 40% solution)
                │
                └── Report Generator Agent
```

## Usage

### Via Cursor Slack App

```bash
/ideation evaluate "Legal research is too time-consuming and expensive"
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `MEM0_API_KEY` | Yes | Mem0 cloud storage |

## Context Sharing via Mem0

Each agent reads/writes to Mem0 using the session_id:

```json
{
  "session_id": "abc123",
  "problem": "Legal research is too time-consuming",
  "threshold": 5.0,
  "phases": {
    "researcher": { "status": "complete", "output": "..." },
    "market_analyst": { "status": "pending" }
  },
  "scores": {
    "problem": 7.2,
    "solution": null,
    "combined": null
  }
}
```

## Features

- **Problem-First Validation**: Validates the problem before evaluating the solution
- **Early Elimination**: Stops immediately if problem validation fails
- **Minimal Agent Repos**: Just CLAUDE.md instructions - no code needed
- **claude.ai/code Execution**: Slack webhook triggers Claude Code directly
- **Mem0 Context**: Shared session state across all agents
- **Two-Phase Pipeline**: Problem validation → Solution validation
- **Weighted Scoring**: 60% problem + 40% solution
- **Pivot Suggestions**: Strategic alternatives for eliminated problems

## License

MIT
