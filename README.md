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

# Use sub-agent orchestrator mode
ideation-claude --subagent "Your idea"
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

## Orchestration Modes

The project supports two orchestration modes:

### 1. Direct SDK Mode (default)

Each agent runs as a separate Claude CLI instance with explicit context passing between phases.

```bash
ideation-claude "Your idea"
```

**Characteristics:**
- Python spawns separate Claude instances for each agent
- Context passed explicitly between phases
- More control over each agent's behavior
- Parallel execution via `asyncio.gather()`

### 2. Sub-Agent Mode

A single Claude coordinator instance uses the Task tool to spawn specialized sub-agents.

```bash
ideation-claude --subagent "Your idea"
```

**Characteristics:**
- Single coordinator orchestrates the entire pipeline
- Sub-agents share parent context automatically
- More native to Claude Code architecture
- Sub-agents can spawn their own sub-agents (nested)
- Better for complex multi-step research

| Aspect | Direct SDK | Sub-Agent |
|--------|-----------|-----------|
| Instances | Multiple Claude instances | Single coordinator |
| Context | Explicit passing | Automatic inheritance |
| Control | Fine-grained | Delegated to coordinator |
| Nesting | Manual | Native support |

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
│   ├── main.py                  # CLI interface
│   ├── orchestrator.py          # Direct SDK pipeline with parallel execution
│   ├── orchestrator_subagent.py # Sub-agent orchestrator using Task tool
│   ├── memory.py                # Mem0 integration
│   └── agents/                  # System prompts
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

## GitHub Actions Integration

This project includes a GitHub Actions workflow that allows you to run evaluations automatically or on-demand.

### Setup

1. **Add Secrets to GitHub Repository:**
   - Go to your repository → Settings → Secrets and variables → Actions
   - Add the following secrets:
     - `ANTHROPIC_API_KEY`: Your Anthropic API key (required)
     - `MEM0_API_KEY`: Your Mem0 API key (optional)
     - `OPENAI_API_KEY`: Your OpenAI API key (optional, for local Mem0)

2. **Workflow Triggers:**
   - **Manual Trigger**: Go to Actions → "Ideation Claude Evaluation" → Run workflow
     - Enter your startup idea
     - Set threshold (default: 5.0)
     - Choose orchestrator mode (direct SDK or sub-agent)
   - **Scheduled**: Runs daily at 2 AM UTC (configurable in `.github/workflows/ideation.yml`)
   - **On Push**: Automatically runs when code changes are pushed to `main`

3. **Batch Evaluation:**
   - Create `.github/ideas.txt` with one idea per line
   - The workflow will evaluate all ideas and generate reports
   - Reports are saved as artifacts and can be downloaded

### Example Workflow Usage

```yaml
# Manual trigger via GitHub UI
# Or use GitHub CLI:
gh workflow run ideation.yml -f idea="AI-powered legal research assistant" -f threshold=6.0
```

### Workflow Features

- ✅ Automatic Python environment setup
- ✅ Dependency installation
- ✅ Secure secret management
- ✅ Report artifact generation
- ✅ PR comment integration (for pull requests)
- ✅ Support for both orchestrator modes

### Privacy Considerations for Public Repositories

⚠️ **Important**: In public repositories, GitHub Actions workflow runs are **visible to everyone** by default. This means:

- Your startup ideas (workflow inputs) are visible in the Actions tab
- Evaluation results and logs are publicly accessible
- Artifacts may be visible (depending on settings)

**Solutions:**

1. **Use Private Workflow** (Recommended for sensitive ideas):
   - Use `.github/workflows/ideation-private.yml` instead
   - Only supports manual triggers (no scheduled/push triggers)
   - Artifacts auto-delete after 1 day
   - Still visible in public repos, but less likely to be discovered

2. **Use a Private Repository**:
   - Fork this repo to a private repository
   - Run evaluations there
   - Keep the public repo for code sharing only

3. **Run Locally**:
   - Use the CLI directly on your machine
   - No workflow runs = no public visibility
   - Best option for highly sensitive ideas

4. **GitHub Pro/Team Feature** (if available):
   - Some GitHub plans support private workflows
   - Check your plan's features

**API Keys are Safe**: Secrets stored in GitHub Secrets are masked in logs and never exposed, even in public repos.

📖 **See `.github/PRIVACY.md` for detailed privacy guidance and solutions.**

## License

MIT
