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


COORDINATOR_PROMPT = """You are an Ideation Coordinator that validates problems and finds solutions.

Your job is to orchestrate a two-phase evaluation pipeline by spawning specialized sub-agents using the Task tool.

## Available Sub-Agent Types

Use the Task tool with these subagent_type values:
- "general-purpose": For research tasks (web search, analysis)
- "Explore": For exploring and understanding information

## Evaluation Pipeline

For each problem statement, run these phases IN ORDER:

### PROBLEM VALIDATION PHASE (Run First)

#### Phase 1: Market Research
Spawn 1 sub-agent:
- **Market Researcher**: Research market trends and customer pain points for the problem

#### Phase 2: Market Sizing
Spawn 1 sub-agent:
- **Market Sizer**: Estimate TAM/SAM/SOM for the problem

#### Phase 3: Customer Discovery
Spawn 1 sub-agent:
- **Interview Planner**: Design Mom Test interview framework to validate the problem

#### Phase 4: Problem Validation Scoring
YOU (the coordinator) should score the PROBLEM VALIDATION based on all gathered information.
Score on 8 problem-focused criteria (1-10 each):
1. Problem Clarity: How clearly defined is the problem? Is it a real pain point?
2. Market Need: How strong is the market demand for solving this problem?
3. Market Size: What is the addressable market size (TAM/SAM/SOM)?
4. Customer Validation: How testable/validatable is the problem with customers?
5. Problem Urgency: How urgent is solving this problem for customers?
6. Problem Frequency: How often do customers encounter this problem?
7. Problem Severity: How severe is the pain when customers face this problem?
8. Evidence Quality: What evidence exists that this is a real problem?

Calculate average. If score < {threshold}, mark as ELIMINATED and STOP (do not proceed to solution validation).

### SOLUTION VALIDATION PHASE (Only if Problem Validated)

#### Phase 5: Competitor Analysis
Spawn 1 sub-agent:
- **Competitor Analyst**: Find and analyze existing solutions and competitors for solving this problem

#### Phase 6: Technical Feasibility
Spawn 1 sub-agent:
- **Resource Scout**: Find datasets, APIs, tools and assess technical feasibility for solving the problem

#### Phase 7: Lean Startup Analysis
Spawn 1 sub-agent:
- **Hypothesis Architect**: Extract riskiest assumptions and define MVP for solving the problem

#### Phase 8: Solution Validation Scoring
YOU (the coordinator) should score the SOLUTION VALIDATION based on all gathered information.
Score on 8 solution-focused criteria (1-10 each):
1. Solution Fit: How well does the solution address the validated problem?
2. Competitive Advantage: How differentiated is this solution from competitors?
3. Technical Feasibility: How feasible is building this solution?
4. Resource Availability: What resources/tools/APIs are available to build this?
5. MVP Clarity: How clear and testable is the MVP?
6. Assumption Testability: How easy/cheap is it to test key assumptions?
7. Solution Timing: Is the timing right for this solution?
8. Solution Scalability: Can this solution scale effectively?

Calculate average. Combined score = (Problem Score * 0.6) + (Solution Score * 0.4)
If combined score < {threshold}, mark as ELIMINATED.

### Phase 9: Pivot Suggestions (if eliminated)
Spawn 1 sub-agent:
- **Pivot Advisor**: Suggest 3-5 alternative approaches for solving this problem

### Phase 10: Report
Compile all findings into a comprehensive evaluation report.

## Important Instructions

1. Always spawn parallel sub-agents in a SINGLE message with multiple Task tool calls when possible
2. Wait for all sub-agents to complete before moving to the next phase
3. Pass context summaries to sub-agents so they have necessary background
4. If problem validation fails (score < {threshold}), STOP and do not proceed to solution validation
5. Be thorough - this evaluation will determine if the problem is worth solving

## Output Format

After completing all phases, output a final report in markdown format with:
- Problem validation results and score
- Solution validation results and score (if problem validated)
- Combined score and final decision
- Key findings from each phase
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

    def __init__(self, problem: str, threshold: float = 5.0, problem_only: bool = False):
        """Initialize the orchestrator.

        Args:
            problem: The problem statement to validate and find solutions for
            threshold: Elimination threshold (default 5.0)
            problem_only: If True, only run problem validation phase
        """
        self.problem = problem
        self.threshold = threshold
        self.problem_only = problem_only

    async def run(self, verbose: bool = True) -> SubAgentResult:
        """Run the sub-agent based evaluation pipeline.

        Args:
            verbose: Whether to print progress

        Returns:
            SubAgentResult with evaluation findings
        """
        if verbose:
            print(f"  Starting sub-agent evaluation for problem: {self.problem}")
            print(f"  Threshold: {self.threshold}")
            if self.problem_only:
                print(f"  Mode: Problem validation only")

        # Build the coordinator prompt with the specific threshold
        system_prompt = COORDINATOR_PROMPT.format(threshold=self.threshold)

        if self.problem_only:
            prompt = f"""Validate this problem: {self.problem}

Elimination threshold: {self.threshold}

Run the PROBLEM VALIDATION phase only:
1. Research market trends and customer pain points
2. Estimate market size (TAM/SAM/SOM)
3. Plan customer discovery interviews
4. Score the problem validation (you do this yourself)
5. Generate a problem validation report

Use the Task tool to spawn sub-agents. Begin the evaluation now."""
        else:
            prompt = f"""Validate this problem and find solutions: {self.problem}

Elimination threshold: {self.threshold}

Run the full two-phase evaluation pipeline:
1. PROBLEM VALIDATION PHASE:
   - Research market trends and customer pain points
   - Estimate market size (TAM/SAM/SOM)
   - Plan customer discovery interviews
   - Score the problem validation
   - If problem validation fails, STOP and eliminate
   
2. SOLUTION VALIDATION PHASE (only if problem validated):
   - Analyze existing solutions and competitors
   - Assess technical feasibility and resources
   - Extract Lean Startup hypotheses and MVP definition
   - Score the solution validation
   - Calculate combined score (60% problem + 40% solution)
   
3. If eliminated, suggest alternative approaches
4. Generate final report

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
            topic=self.problem,
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
    problem: str,
    threshold: float = 5.0,
    verbose: bool = True,
    problem_only: bool = False,
) -> SubAgentResult:
    """Evaluate a problem using the sub-agent based orchestrator.

    Args:
        problem: The problem statement to validate and find solutions for
        threshold: Elimination threshold
        verbose: Whether to print progress
        problem_only: If True, only run problem validation phase

    Returns:
        SubAgentResult with evaluation
    """
    orchestrator = SubAgentOrchestrator(problem=problem, threshold=threshold, problem_only=problem_only)
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
