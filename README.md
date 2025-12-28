# Ideation-Claude

Multi-agent startup idea validator using Claude CLI instances.

Unlike traditional agent frameworks (CrewAI, LangChain), this project runs each agent as a **real Claude Code CLI instance**, leveraging the full power of Claude's capabilities including web search, file operations, and tool use.

## Features

- **9 Specialized Agents**: Each with a specific role in the validation pipeline
- **Session-Based Context**: Agents share context through Claude's session management
- **Lean Startup Methodology**: Hypothesis extraction and MVP definition
- **Mom Test Framework**: Customer discovery interview planning
- **8-Criteria Scoring**: Objective evaluation with go/no-go decisions
- **Pivot Suggestions**: Strategic alternatives for eliminated ideas
- **Memory Integration**: Track previously eliminated ideas with Mem0

## Pipeline

```
1. Researcher        → Market trends & pain points
2. Competitor Analyst → Competitive landscape
3. Market Analyst    → TAM/SAM/SOM sizing
4. Resource Scout    → Datasets, APIs, tools
5. Hypothesis Architect → Lean Startup assumptions & MVP
6. Customer Discovery → Mom Test interview planning
7. Scoring Evaluator → 8-criteria evaluation
8. Pivot Advisor     → Suggestions for eliminated ideas
9. Report Generator  → Final evaluation report
```

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
- Session context from previous agents

The orchestrator manages the pipeline, passing session IDs between agents to maintain context.

## Comparison to CrewAI

| Aspect | CrewAI | Ideation-Claude |
|--------|--------|-----------------|
| Agent runtime | LLM API calls | Real Claude CLI instances |
| Tools | Framework wrappers | Native Claude tools |
| Context | Task parameters | Session resume |
| Overhead | Heavy framework | Minimal SDK |

## License

MIT
