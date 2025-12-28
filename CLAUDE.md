# Ideation Orchestrator

This is the central orchestrator for the Ideation multi-agent pipeline. It coordinates individual agent repos via webhook triggers and uses Mem0 for shared context.

## Architecture

```
                    ┌─────────────────────────┐
                    │   ideation-orchestrator │
                    │   (this repo)           │
                    └───────────┬─────────────┘
                                │
               ┌────────────────┼────────────────┐
               │                │                │
               ▼                ▼                ▼
    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
    │  researcher  │  │ market-      │  │ customer-    │
    │              │  │ analyst      │  │ discovery    │
    └──────────────┘  └──────────────┘  └──────────────┘
               ...              ...              ...
```

## Agent Repos

The orchestrator invokes these 9 agent repos via GitHub `repository_dispatch`:

1. [ideation-agent-researcher](https://github.com/Othentic-Ai/ideation-agent-researcher)
2. [ideation-agent-market-analyst](https://github.com/Othentic-Ai/ideation-agent-market-analyst)
3. [ideation-agent-customer-discovery](https://github.com/Othentic-Ai/ideation-agent-customer-discovery)
4. [ideation-agent-scoring-evaluator](https://github.com/Othentic-Ai/ideation-agent-scoring-evaluator)
5. [ideation-agent-competitor-analyst](https://github.com/Othentic-Ai/ideation-agent-competitor-analyst)
6. [ideation-agent-resource-scout](https://github.com/Othentic-Ai/ideation-agent-resource-scout)
7. [ideation-agent-hypothesis-architect](https://github.com/Othentic-Ai/ideation-agent-hypothesis-architect)
8. [ideation-agent-pivot-advisor](https://github.com/Othentic-Ai/ideation-agent-pivot-advisor)
9. [ideation-agent-report-generator](https://github.com/Othentic-Ai/ideation-agent-report-generator)

## Evaluation Flow

1. Orchestrator receives problem statement (via Slack or CLI)
2. Creates session in Mem0 with unique session_id
3. Triggers agents via `repository_dispatch` webhooks
4. Each agent reads context from Mem0, executes, writes results back
5. Orchestrator polls Mem0 for completion, continues to next phase
6. Final report generated and returned

## Usage

### Via CLI

```bash
# Evaluate a problem using webhook-triggered agents
ideation-claude evaluate "Your problem statement" --webhook

# Or using the Python API
from ideation_claude.orchestrator_webhook import evaluate_with_webhooks
result = evaluate_with_webhooks("Your problem statement")
```

### Via Cursor Slack App

The orchestrator can be triggered via Cursor Slack app, which fires a webhook to start the evaluation pipeline.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GITHUB_TOKEN` | Yes | Token with repo dispatch permissions |
| `ANTHROPIC_API_KEY` | Yes | For Claude API access |
| `MEM0_API_KEY` | Yes | For Mem0 cloud storage |

## Local Development

The orchestrator also supports running agents locally (without webhooks) for development:

```bash
# Run with local agents (subagent mode)
ideation-claude evaluate "Your problem statement"
```
