"""Alternative orchestrator using Claude's native sub-agent Task tool.

Instead of spawning separate Claude instances, this orchestrator runs
a single Claude coordinator that uses the Task tool to spawn specialized
sub-agents for each phase of the evaluation pipeline.

Benefits:
- Sub-agents share parent context automatically
- More native to Claude Code architecture
- Sub-agents can spawn their own sub-agents (nested)
- Better for complex multi-step research
"""

import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from claude_code_sdk import query, ClaudeCodeOptions


COORDINATOR_PROMPT = """You are an Ideation Coordinator that evaluates startup ideas.

Your job is to orchestrate a multi-phase evaluation pipeline by spawning specialized sub-agents using the Task tool.

## Available Sub-Agent Types

Use the Task tool with these subagent_type values:
- "general-purpose": For research tasks (web search, analysis)
- "Explore": For exploring and understanding information

## Evaluation Pipeline

For each startup idea, run these phases IN ORDER:

### Phase 1: Research (spawn in parallel)
Spawn 3 sub-agents simultaneously:
1. **Market Researcher**: Research market trends and customer pain points
2. **Competitor Analyst**: Find and analyze competitors
3. **Market Sizer**: Estimate TAM/SAM/SOM

### Phase 2: Technical Assessment
Spawn 1 sub-agent:
- **Resource Scout**: Find datasets, APIs, tools and assess technical feasibility

### Phase 3: Lean Startup Analysis
Spawn 1 sub-agent:
- **Hypothesis Architect**: Extract riskiest assumptions and define MVP

### Phase 4: Customer Discovery
Spawn 1 sub-agent:
- **Interview Planner**: Design Mom Test interview framework

### Phase 5: Scoring
YOU (the coordinator) should score the idea based on all gathered information.
Score on 8 criteria (1-10 each):
1. Market Size
2. Competition (inverted - low competition = high score)
3. Differentiation
4. Technical Feasibility
5. Timing
6. Resource Availability
7. Assumption Testability
8. Evidence Quality

Calculate average. If score < {threshold}, mark as ELIMINATED.

### Phase 6: Pivot Suggestions (if eliminated)
Spawn 1 sub-agent:
- **Pivot Advisor**: Suggest 3-5 strategic pivots

### Phase 7: Report
Compile all findings into a comprehensive evaluation report.

## Important Instructions

1. Always spawn parallel sub-agents in a SINGLE message with multiple Task tool calls
2. Wait for all sub-agents to complete before moving to the next phase
3. Pass context summaries to sub-agents so they have necessary background
4. Be thorough - this evaluation will determine if the idea is worth pursuing

## Output Format

After completing all phases, output a final report in markdown format.
"""


@dataclass
class SubAgentResult:
    """Result from the sub-agent based evaluation."""
    topic: str
    report: str = ""
    total_score: float = 0.0
    eliminated: bool = False
    raw_output: str = ""


class SubAgentOrchestrator:
    """Orchestrator that uses Claude's native sub-agent capabilities.

    Instead of spawning separate Claude instances for each agent,
    this orchestrator runs a single Claude coordinator that uses
    the Task tool to spawn specialized sub-agents.
    """

    def __init__(self, topic: str, threshold: float = 5.0):
        """Initialize the orchestrator.

        Args:
            topic: The startup idea/topic to evaluate
            threshold: Elimination threshold (default 5.0)
        """
        self.topic = topic
        self.threshold = threshold

    async def run(self, verbose: bool = True) -> SubAgentResult:
        """Run the sub-agent based evaluation pipeline.

        Args:
            verbose: Whether to print progress

        Returns:
            SubAgentResult with evaluation findings
        """
        if verbose:
            print(f"  Starting sub-agent evaluation for: {self.topic}")
            print(f"  Threshold: {self.threshold}")

        # Build the coordinator prompt with the specific topic
        system_prompt = COORDINATOR_PROMPT.format(threshold=self.threshold)

        prompt = f"""Evaluate this startup idea: {self.topic}

Elimination threshold: {self.threshold}

Run the full evaluation pipeline:
1. Spawn parallel sub-agents for research (market, competitors, sizing)
2. Assess technical feasibility and resources
3. Extract Lean Startup hypotheses and MVP definition
4. Plan customer discovery interviews
5. Score the opportunity (you do this yourself)
6. If eliminated, suggest pivots
7. Generate final report

Use the Task tool to spawn sub-agents. For parallel tasks, include multiple Task calls in a single message.

Begin the evaluation now."""

        options = ClaudeCodeOptions(
            system_prompt=system_prompt,
            max_turns=50,  # Allow many turns for complex multi-agent orchestration
        )

        result_parts = []

        async for message in query(prompt=prompt, options=options):
            if hasattr(message, "content"):
                content = str(message.content)
                result_parts.append(content)
                if verbose and content.strip():
                    # Print progress indicators
                    if "Phase" in content or "Spawning" in content or "Score" in content:
                        print(f"  {content[:100]}...")

        raw_output = "\n".join(result_parts)

        # Extract score and elimination status from output
        total_score = self._extract_score(raw_output)
        eliminated = total_score < self.threshold or "ELIMINATED" in raw_output.upper()

        return SubAgentResult(
            topic=self.topic,
            report=raw_output,
            total_score=total_score,
            eliminated=eliminated,
            raw_output=raw_output,
        )

    def _extract_score(self, text: str) -> float:
        """Extract the total score from output."""
        import re
        patterns = [
            # Markdown table: | **TOTAL** | **6.25/10** |
            r"\*\*TOTAL\*\*\s*\|\s*\*\*(\d+\.?\d*)/10\*\*",
            # Bold total: **TOTAL**: **6.5/10**
            r"\*\*TOTAL\*\*[:\s]*\*\*(\d+\.?\d*)/10\*\*",
            # Plain: TOTAL: 6.5/10 or Total: 6.5/10
            r"TOTAL[:\s]*(\d+\.?\d*)/10",
            r"Total[:\s]*(\d+\.?\d*)/10",
            # Average: 6.5/10
            r"Average[:\s]*(\d+\.?\d*)/10",
            # Score header: **Score**: 6.25/10
            r"\*\*Score\*\*[:\s]*(\d+\.?\d*)/10",
            # Generic: Score: 6.5/10
            r"Score[:\s]*(\d+\.?\d*)/10",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return float(match.group(1))
        return 0.0


async def evaluate_with_subagents(
    topic: str,
    threshold: float = 5.0,
    verbose: bool = True,
) -> SubAgentResult:
    """Evaluate an idea using the sub-agent based orchestrator.

    Args:
        topic: The startup idea to evaluate
        threshold: Elimination threshold
        verbose: Whether to print progress

    Returns:
        SubAgentResult with evaluation
    """
    orchestrator = SubAgentOrchestrator(topic=topic, threshold=threshold)
    return await orchestrator.run(verbose=verbose)


# Comparison of approaches:
#
# 1. Direct SDK Orchestrator (orchestrator.py):
#    - Python spawns separate Claude instances for each agent
#    - Context passed explicitly between phases
#    - More control over each agent's behavior
#    - Parallel execution via asyncio.gather()
#
# 2. Sub-Agent Orchestrator (this file):
#    - Single Claude coordinator instance
#    - Uses Task tool to spawn sub-agents
#    - Sub-agents share parent context automatically
#    - More native to Claude Code architecture
#    - Coordinator handles scoring and final synthesis
