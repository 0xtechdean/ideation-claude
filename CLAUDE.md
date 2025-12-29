# Ideation Orchestrator

Central orchestrator for the Ideation multi-agent pipeline. Coordinates agent repos via Slack webhook → claude.ai/code and uses Mem0 for shared context.

## Architecture

```
Slack (/ideation evaluate "problem")
         │
         ▼
    claude.ai/code
         │
         ├──▶ ideation-agent-researcher
         ├──▶ ideation-agent-market-analyst
         ├──▶ ideation-agent-customer-discovery
         ├──▶ ideation-agent-scoring-evaluator
         ├──▶ ideation-agent-competitor-analyst
         ├──▶ ideation-agent-resource-scout
         ├──▶ ideation-agent-hypothesis-architect
         ├──▶ ideation-agent-pivot-advisor
         └──▶ ideation-agent-report-generator
                    │
                    ▼
                  Mem0 (shared context)
```

## Agent Repos

Each agent is a minimal repo with just `CLAUDE.md`:

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

1. Slack receives `/ideation evaluate "problem"`
2. Slack app triggers claude.ai/code with agent repo URL
3. Claude Code reads agent's CLAUDE.md, executes
4. Agent writes results to Mem0 under session_id
5. Next agent triggered, reads previous context from Mem0
6. Final report posted back to Slack

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `MEM0_API_KEY` | Yes | For Mem0 cloud storage |
| `OPENAI_API_KEY` | Yes | For Mem0 embeddings |
