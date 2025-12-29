# Ideation-Claude

Multi-agent startup problem validator using Claude Code.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Cursor Slack App                             │
│              /ideation evaluate "problem"                        │
└─────────────────────────────┬───────────────────────────────────┘
                              │ triggers
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR (this repo)                      │
│         claude.ai/code reads CLAUDE.md, manages flow             │
│                              │                                   │
│    ┌─────────────────────────┼─────────────────────────┐        │
│    │ Uses Slack hooks to     │                         │        │
│    │ invoke sub-agents:      ▼                         │        │
│    │                   ┌───────────┐                   │        │
│    │  researcher ────▶ │   Mem0    │ ◀──── scoring     │        │
│    │  market-analyst ▶ │ (context) │ ◀──── pivot       │        │
│    │  customer-disc ─▶ │           │ ◀──── report      │        │
│    │                   └───────────┘                   │        │
│    └───────────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────────┘
```

## How It Works

1. User in Slack: `/ideation evaluate "Legal research is too expensive"`
2. Slack App triggers claude.ai/code with **this orchestrator repo**
3. Orchestrator reads CLAUDE.md and manages the entire flow
4. For each agent, Orchestrator uses Slack hooks to invoke:
   ```
   /claude run github.com/Othentic-Ai/ideation-agent-{name}
   ```
5. Each agent reads context from Mem0, executes, writes results back
6. Orchestrator checks Mem0 for completion, handles scoring decisions
7. Orchestrator continues to next agent or eliminates based on score
8. Final report returned to Slack

## Agent Repositories

Each agent is a minimal repo with just `CLAUDE.md`:

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

## Evaluation Pipeline

```
ORCHESTRATOR manages this flow:

PROBLEM VALIDATION PHASE
├── 1. Researcher Agent (trends & pain points)
├── 2. Market Analyst Agent (TAM/SAM/SOM)
├── 3. Customer Discovery Agent (Mom Test)
└── 4. Scoring Evaluator Agent (problem score)
        │
        ├── Score < 5.0? → ELIMINATE → Pivot Advisor → Report
        │
        └── Score >= 5.0? → Continue ↓

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

```bash
/ideation evaluate "Legal research is too time-consuming and expensive"
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `MEM0_API_KEY` | Yes | Mem0 cloud storage |

## Context Sharing via Mem0

Orchestrator and all agents read/write to Mem0 using the session_id:

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

- **Orchestrator-Managed Flow**: Single orchestrator controls entire pipeline
- **Slack Hooks for Sub-Agents**: Orchestrator invokes agents via Slack
- **Problem-First Validation**: Validates problem before solution
- **Early Elimination**: Stops immediately if score < 5.0
- **Mem0 Context**: Shared session state across all agents
- **Weighted Scoring**: 60% problem + 40% solution

## License

MIT
