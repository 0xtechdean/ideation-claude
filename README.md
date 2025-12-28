# Ideation-Claude

Multi-agent startup idea validator using Claude CLI instances.

Unlike traditional agent frameworks (CrewAI, LangChain), this project runs each agent as a **real Claude Code CLI instance**, leveraging the full power of Claude's capabilities including web search, file operations, and tool use.

## Features

- **9 Specialized Agents**: Each with a specific role in the validation pipeline
- **Parallel Execution**: Independent agents run concurrently for faster evaluation
- **Lean Startup Methodology**: Hypothesis extraction and MVP definition
- **Mom Test Framework**: Customer discovery interview planning
- **8-Criteria Scoring**: Objective evaluation with go/no-go decisions
- **Pivot Suggestions**: Strategic alternatives for eliminated ideas
- **Memory Integration**: Track previously eliminated ideas with Mem0

## Pipeline (Optimized with Parallel Execution)

```
Phase 1: Research
            ↓
Phase 2: ┌─ Competitor Analysis ─┐
         ├─ Market Sizing       ─┼─ (parallel)
         └─ Resource Discovery  ─┘
            ↓
Phase 3: Hypothesis & MVP (Lean Startup)
            ↓
Phase 4: Customer Discovery (Mom Test)
            ↓
Phase 5: Scoring (8 criteria)
            ↓
Phase 6: ┌─ Pivot Suggestions ─┐
         └─ Report Generation ─┘ (parallel, if eliminated)
```

**9 agents, 6 phases** - Parallel execution reduces evaluation time significantly.

## Installation

```bash
# Clone the repo
git clone https://github.com/0xtechdean/ideation-claude.git
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

## Usage

```bash
# Evaluate a startup idea
ideation-claude "AI-powered legal research assistant"

# Evaluate multiple ideas
ideation-claude "Legal AI" "Sustainable packaging marketplace"

# Interactive mode
ideation-claude --interactive

# With custom threshold (default: 5.0)
ideation-claude --threshold 6.0 "Your idea"

# Save report to file
ideation-claude --output report.md "Your idea"
```

## Requirements

- Python 3.10+
- Claude Code CLI installed and authenticated
- Anthropic API key (for Claude)
- Mem0 API key (optional, for cloud memory)
- OpenAI API key (for local Mem0 embeddings)

## Environment Variables

```bash
ANTHROPIC_API_KEY=your_key_here
MEM0_API_KEY=your_key_here  # Optional
OPENAI_API_KEY=your_key_here  # For local Mem0
```

## Architecture

Each agent is a Claude CLI invocation with:
- A specialized system prompt (`.md` file)
- Access to specific tools (WebSearch, Read, etc.)
- Context passed explicitly between phases

The orchestrator manages the pipeline using `asyncio.gather()` to run independent agents in parallel.

### Agent Details

| Agent | Role | Tools |
|-------|------|-------|
| Researcher | Market trends & pain points | WebSearch |
| Competitor Analyst | Competitive landscape | WebSearch |
| Market Analyst | TAM/SAM/SOM sizing | WebSearch |
| Resource Scout | Datasets, APIs, tools | WebSearch |
| Hypothesis Architect | Lean Startup assumptions | - |
| Customer Discovery | Mom Test interview planning | - |
| Scoring Evaluator | 8-criteria scoring | - |
| Pivot Advisor | Strategic alternatives | - |
| Report Generator | Final evaluation report | - |

## Comparison to CrewAI

| Aspect | CrewAI | Ideation-Claude |
|--------|--------|-----------------|
| Agent runtime | LLM API calls | Real Claude CLI instances |
| Tools | Framework wrappers | Native Claude tools |
| Context | Task parameters | Explicit context passing |
| Parallelism | Sequential by default | Parallel by default |
| Overhead | Heavy framework | Minimal SDK |

## Project Structure

```
ideation-claude/
├── src/ideation_claude/
│   ├── main.py              # CLI interface
│   ├── orchestrator.py      # Pipeline with parallel execution
│   ├── memory.py            # Mem0 integration
│   └── agents/              # System prompts
│       ├── researcher.md
│       ├── competitor_analyst.md
│       ├── market_analyst.md
│       ├── resource_scout.md
│       ├── hypothesis_architect.md
│       ├── customer_discovery.md
│       ├── scoring_evaluator.md
│       ├── pivot_advisor.md
│       └── report_generator.md
├── pyproject.toml
└── .env.example
```

## License

MIT
