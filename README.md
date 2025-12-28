# Ideation-Claude (Orchestrator)

Multi-agent problem validator and solution finder using Claude CLI instances.

This is the **central orchestrator** that coordinates 9 specialized agent repositories via webhook triggers (for Cursor Slack app integration) or local sub-agents (for development).

## Distributed Architecture

```
                        ┌─────────────────────────────┐
                        │   Cursor Slack App          │
                        │   /ideation evaluate "..."  │
                        └──────────────┬──────────────┘
                                       │
                                       ▼
┌──────────────────────────────────────────────────────────────────┐
│                    IDEATION ORCHESTRATOR                          │
│                    (this repository)                              │
│  • Triggers agents via repository_dispatch webhooks               │
│  • Polls Mem0 for completion                                      │
│  • Manages session context                                        │
└───────────────────────────┬──────────────────────────────────────┘
                            │
              ┌─────────────┴─────────────┐
              │         Mem0              │
              │   (Shared Context)        │
              └─────────────┬─────────────┘
                            │
    ┌───────────────────────┼───────────────────────┐
    │                       │                       │
    ▼                       ▼                       ▼
┌─────────┐           ┌─────────┐           ┌─────────┐
│researcher│          │ market- │           │customer-│
│         │          │ analyst │           │discovery│
└─────────┘           └─────────┘           └─────────┘
    │                       │                       │
    └───────────────────────┼───────────────────────┘
                            │
    ┌───────────────────────┼───────────────────────┐
    │                       │                       │
    ▼                       ▼                       ▼
┌─────────┐           ┌─────────┐           ┌─────────┐
│scoring- │           │competitor│          │resource-│
│evaluator│           │-analyst │           │ scout   │
└─────────┘           └─────────┘           └─────────┘
    │                       │                       │
    └───────────────────────┼───────────────────────┘
                            │
    ┌───────────────────────┼───────────────────────┐
    │                       │                       │
    ▼                       ▼                       ▼
┌─────────┐           ┌─────────┐           ┌─────────┐
│hypothesis│          │  pivot- │           │ report- │
│-architect│          │ advisor │           │generator│
└─────────┘           └─────────┘           └─────────┘
```

## Agent Repositories

Each agent lives in its own public repository under [Othentic-Ai](https://github.com/Othentic-Ai):

| Agent | Repository | Description |
|-------|------------|-------------|
| Researcher | [ideation-agent-researcher](https://github.com/Othentic-Ai/ideation-agent-researcher) | Market trends & pain points |
| Market Analyst | [ideation-agent-market-analyst](https://github.com/Othentic-Ai/ideation-agent-market-analyst) | TAM/SAM/SOM calculations |
| Customer Discovery | [ideation-agent-customer-discovery](https://github.com/Othentic-Ai/ideation-agent-customer-discovery) | Mom Test interview framework |
| Scoring Evaluator | [ideation-agent-scoring-evaluator](https://github.com/Othentic-Ai/ideation-agent-scoring-evaluator) | 8-criteria opportunity scoring |
| Competitor Analyst | [ideation-agent-competitor-analyst](https://github.com/Othentic-Ai/ideation-agent-competitor-analyst) | Competitive landscape analysis |
| Resource Scout | [ideation-agent-resource-scout](https://github.com/Othentic-Ai/ideation-agent-resource-scout) | Technical feasibility & resources |
| Hypothesis Architect | [ideation-agent-hypothesis-architect](https://github.com/Othentic-Ai/ideation-agent-hypothesis-architect) | Lean Startup framework & MVP |
| Pivot Advisor | [ideation-agent-pivot-advisor](https://github.com/Othentic-Ai/ideation-agent-pivot-advisor) | Strategic alternatives |
| Report Generator | [ideation-agent-report-generator](https://github.com/Othentic-Ai/ideation-agent-report-generator) | Final evaluation report |

Each agent repo contains:
- Full Python package with CLI
- GitHub Actions with `repository_dispatch` trigger
- Mem0 integration for shared session context
- Claude Code system prompt

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

### Via Cursor Slack App (Webhook Mode)

Trigger the orchestrator via Slack, which fires webhooks to each agent:

```bash
/ideation evaluate "Legal research is too time-consuming and expensive"
```

### Via CLI (Local Mode)

Run with local sub-agents (for development):

```bash
# Install
pip install -e .

# Evaluate a problem
ideation-claude "Legal research is too time-consuming and expensive"

# With custom threshold
ideation-claude --threshold 6.0 "Your problem"

# Problem validation only
ideation-claude --problem-only "Your problem"
```

### Via Webhook Trigger (Direct)

Trigger agents directly via GitHub API:

```bash
# Trigger the researcher agent
curl -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/Othentic-Ai/ideation-agent-researcher/dispatches \
  -d '{"event_type": "run", "client_payload": {"session_id": "abc123", "problem": "Your problem"}}'
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Claude API access |
| `MEM0_API_KEY` | Yes | Mem0 cloud storage |
| `GITHUB_TOKEN` | For webhooks | Token with repo dispatch permissions |
| `OPENAI_API_KEY` | For local Mem0 | Embeddings (if not using Mem0 cloud) |

## How Context Sharing Works

1. **Session Creation**: Orchestrator creates a session in Mem0 with unique `session_id`
2. **Agent Execution**: Each agent reads context from Mem0, executes, writes results back
3. **Polling**: Orchestrator polls Mem0 for phase completion
4. **Continuation**: Next agent is triggered with accumulated context

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
- **Distributed Agents**: Each agent in its own repo for independent scaling
- **Webhook Triggers**: Invoke via Cursor Slack app or GitHub API
- **Mem0 Context**: Shared session state across all agents
- **Two-Phase Pipeline**: Problem validation → Solution validation
- **Weighted Scoring**: 60% problem + 40% solution
- **Pivot Suggestions**: Strategic alternatives for eliminated problems

## Project Structure

```
ideation-claude/
├── src/ideation_claude/
│   ├── main.py                    # CLI interface
│   ├── orchestrator_webhook.py    # Webhook-based orchestration
│   ├── orchestrator_subagent.py   # Local sub-agent orchestration
│   ├── orchestrator.py            # Legacy direct SDK (not used)
│   ├── memory.py                  # Mem0 integration
│   └── agents/                    # Local agent prompts (for dev)
├── .github/workflows/
│   └── ideation.yml               # GitHub Actions workflow
├── CLAUDE.md                      # Claude Code instructions
└── README.md
```

## Installation

```bash
# Clone the orchestrator
git clone https://github.com/Othentic-Ai/ideation-claude.git
cd ideation-claude

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e .

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys
```

## Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=src/ideation_claude --cov-report=html
```

## License

MIT
