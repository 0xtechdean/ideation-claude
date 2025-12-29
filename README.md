# Ideation-Claude

Multi-agent startup problem validator using Claude Code.

## Architecture

```mermaid
graph TB
    subgraph "Slack Interface"
        SLACK[/ideation evaluate]
    end

    subgraph "Orchestration Layer"
        ORCH[Ideation Orchestrator]
    end

    subgraph "Evaluation Pipeline"
        PHASE1[Phase 1: Market Research]
        PHASE2[Phase 2: Competitive Analysis]
        PHASE3[Phase 3: Market Sizing]
        PHASE4[Phase 4: Technical Feasibility]
        PHASE5[Phase 5: Lean Startup]
        PHASE6[Phase 6: Mom Test]
        PHASE7[Phase 7: Scoring]
        PHASE8[Phase 8: Pivot Suggestions]
    end

    subgraph "Agents"
        AGENT1[Market Research Agent]
        AGENT2[Competitive Analysis Agent]
        AGENT3[Market Sizing Agent]
        AGENT4[Technical Feasibility Agent]
        AGENT5[Lean Startup Agent]
        AGENT6[Mom Test Agent]
        AGENT7[Scoring Agent]
        AGENT8[Pivot Agent]
    end

    subgraph "Memory & Context"
        MEM0[Mem0 Memory Service]
        CONTEXT[Past Evaluations<br/>Phase Outputs<br/>Market Insights]
    end

    SLACK --> ORCH
    ORCH --> PHASE1
    ORCH --> PHASE2
    ORCH --> PHASE3
    ORCH --> PHASE4
    ORCH --> PHASE5
    ORCH --> PHASE6
    ORCH --> PHASE7
    ORCH --> PHASE8

    PHASE1 --> AGENT1
    PHASE2 --> AGENT2
    PHASE3 --> AGENT3
    PHASE4 --> AGENT4
    PHASE5 --> AGENT5
    PHASE6 --> AGENT6
    PHASE7 --> AGENT7
    PHASE8 --> AGENT8

    AGENT1 --> MEM0
    AGENT2 --> MEM0
    AGENT3 --> MEM0
    AGENT4 --> MEM0
    AGENT5 --> MEM0
    AGENT6 --> MEM0
    AGENT7 --> MEM0
    AGENT8 --> MEM0

    MEM0 --> CONTEXT
    CONTEXT --> AGENT1
    CONTEXT --> AGENT2
    CONTEXT --> AGENT3
    CONTEXT --> AGENT4
    CONTEXT --> AGENT5
    CONTEXT --> AGENT6
    CONTEXT --> AGENT7
    CONTEXT --> AGENT8

    style SLACK fill:#e1f5ff
    style ORCH fill:#fff4e1
    style MEM0 fill:#e8f5e9
```

## How It Works

1. User in Slack: `/ideation evaluate "Legal research is too expensive"`
2. Slack App triggers claude.ai/code with orchestrator repo
3. Orchestrator runs 8 phases sequentially
4. Each agent reads previous context from Mem0
5. Each agent writes its output to Mem0
6. Scoring agent determines pass/eliminate
7. If eliminated, Pivot agent suggests alternatives
8. Final evaluation posted back to Slack

## Agent Repositories

| Phase | Agent | Repository |
|-------|-------|------------|
| 1 | Market Research | [ideation-agent-market-research](https://github.com/Othentic-Ai/ideation-agent-market-research) |
| 2 | Competitive Analysis | [ideation-agent-competitive-analysis](https://github.com/Othentic-Ai/ideation-agent-competitive-analysis) |
| 3 | Market Sizing | [ideation-agent-market-sizing](https://github.com/Othentic-Ai/ideation-agent-market-sizing) |
| 4 | Technical Feasibility | [ideation-agent-technical-feasibility](https://github.com/Othentic-Ai/ideation-agent-technical-feasibility) |
| 5 | Lean Startup | [ideation-agent-lean-startup](https://github.com/Othentic-Ai/ideation-agent-lean-startup) |
| 6 | Mom Test | [ideation-agent-mom-test](https://github.com/Othentic-Ai/ideation-agent-mom-test) |
| 7 | Scoring | [ideation-agent-scoring](https://github.com/Othentic-Ai/ideation-agent-scoring) |
| 8 | Pivot | [ideation-agent-pivot](https://github.com/Othentic-Ai/ideation-agent-pivot) |

### Agent Repo Structure

```
ideation-agent-{name}/
├── CLAUDE.md        # Agent instructions (Claude Code reads this)
└── README.md        # Documentation
```

No Python packages, no GitHub Actions - just instructions for Claude Code.

## Evaluation Pipeline

```
Phase 1: Market Research
    ↓
Phase 2: Competitive Analysis
    ↓
Phase 3: Market Sizing (TAM/SAM/SOM)
    ↓
Phase 4: Technical Feasibility
    ↓
Phase 5: Lean Startup (MVP)
    ↓
Phase 6: Mom Test (Customer Discovery)
    ↓
Phase 7: Scoring
    │
    ├── Score < 5.0 → ELIMINATE → Phase 8: Pivot
    │
    └── Score >= 5.0 → PASSED
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

Each agent reads/writes to Mem0 using the session_id:

```json
{
  "session_id": "abc123",
  "problem": "Legal research is too time-consuming",
  "threshold": 5.0,
  "phases": {
    "market_research": { "status": "complete", "output": "..." },
    "competitive_analysis": { "status": "pending" }
  },
  "score": null,
  "eliminated": false
}
```

## Features

- **8-Phase Pipeline**: Comprehensive evaluation from research to scoring
- **Early Elimination**: Stops at scoring if score < 5.0
- **Minimal Agent Repos**: Just CLAUDE.md instructions - no code needed
- **claude.ai/code Execution**: Slack webhook triggers Claude Code directly
- **Mem0 Context**: Shared session state across all agents
- **Pivot Suggestions**: Strategic alternatives for eliminated problems

## License

MIT
