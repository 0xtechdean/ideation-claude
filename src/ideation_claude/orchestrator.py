"""Orchestrator for running the ideation pipeline using Claude CLI instances."""

import asyncio
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from claude_code_sdk import query, ClaudeCodeOptions


@dataclass
class IdeaResult:
    """Result of evaluating a single startup idea."""

    topic: str
    research_insights: str = ""
    competitor_analysis: str = ""
    market_sizing: str = ""
    resource_findings: str = ""
    hypothesis: str = ""
    customer_discovery: str = ""
    scores: str = ""
    decision: str = ""
    pivot_suggestions: str = ""
    report: str = ""
    total_score: float = 0.0
    eliminated: bool = False
    scoring_iterations: int = 0


@dataclass
class PipelineState:
    """State maintained across the pipeline."""

    topic: str
    threshold: float = 5.0
    session_id: Optional[str] = None
    results: IdeaResult = field(default_factory=lambda: IdeaResult(topic=""))

    def __post_init__(self):
        self.results = IdeaResult(topic=self.topic)


class IdeationOrchestrator:
    """Orchestrates the 9-phase startup evaluation pipeline.

    Each agent runs as a Claude CLI instance with session context
    passed between phases for continuity.
    """

    def __init__(self, topic: str, threshold: float = 5.0):
        """Initialize the orchestrator.

        Args:
            topic: The startup idea/topic to evaluate
            threshold: Elimination threshold (default 5.0)
        """
        self.state = PipelineState(topic=topic, threshold=threshold)
        self.agents_dir = Path(__file__).parent / "agents"

    def _get_agent_prompt(self, agent_name: str) -> str:
        """Load the system prompt for an agent."""
        prompt_file = self.agents_dir / f"{agent_name}.md"
        if not prompt_file.exists():
            raise FileNotFoundError(f"Agent prompt not found: {prompt_file}")
        return prompt_file.read_text()

    async def _run_agent(
        self,
        agent_name: str,
        prompt: str,
        allowed_tools: Optional[list[str]] = None,
    ) -> str:
        """Run a single agent and return its output.

        Args:
            agent_name: Name of the agent (matches .md file)
            prompt: The prompt to send to the agent
            allowed_tools: List of tools the agent can use

        Returns:
            The agent's response text
        """
        system_prompt = self._get_agent_prompt(agent_name)

        options = ClaudeCodeOptions(
            system_prompt=system_prompt,
            allowed_tools=allowed_tools or [],
            max_turns=15,
        )

        # Resume session if we have one (context from previous agents)
        if self.state.session_id:
            options.resume = self.state.session_id

        result_parts = []

        async for message in query(prompt=prompt, options=options):
            # Collect result text
            if hasattr(message, "content"):
                result_parts.append(str(message.content))

            # Capture session ID for next agent
            if hasattr(message, "session_id") and message.session_id:
                self.state.session_id = message.session_id

        return "\n".join(result_parts)

    def _extract_score(self, scoring_text: str) -> float:
        """Extract the total score from scoring output."""
        # Look for patterns like "TOTAL: 6.5/10" or "Total Score: 6.5"
        patterns = [
            r"\*\*TOTAL\*\*[:\s]*\*\*(\d+\.?\d*)/10\*\*",
            r"TOTAL[:\s]*(\d+\.?\d*)/10",
            r"Total Score[:\s]*(\d+\.?\d*)",
            r"Score[:\s]*(\d+\.?\d*)/10",
        ]

        for pattern in patterns:
            match = re.search(pattern, scoring_text, re.IGNORECASE)
            if match:
                return float(match.group(1))

        return 0.0

    def _is_eliminated(self, scoring_text: str) -> bool:
        """Check if the idea was eliminated based on scoring output."""
        return "ELIMINATE" in scoring_text.upper()

    async def run_pipeline(self, verbose: bool = True) -> IdeaResult:
        """Run the full 9-phase evaluation pipeline.

        Args:
            verbose: Whether to print progress messages

        Returns:
            IdeaResult with all findings
        """
        topic = self.state.topic
        results = self.state.results

        def log(msg: str):
            if verbose:
                print(f"  {msg}")

        # Phase 1: Research
        log("[1/9] Researching market trends and pain points...")
        results.research_insights = await self._run_agent(
            "researcher",
            f"Research market trends and customer pain points for: {topic}",
            allowed_tools=["WebSearch"],
        )

        # Phase 2: Competitor Analysis
        log("[2/9] Analyzing competitive landscape...")
        results.competitor_analysis = await self._run_agent(
            "competitor_analyst",
            f"Analyze competitors for: {topic}\n\nUse the research context from the previous phase.",
            allowed_tools=["WebSearch"],
        )

        # Phase 3: Market Sizing
        log("[3/9] Estimating market size (TAM/SAM/SOM)...")
        results.market_sizing = await self._run_agent(
            "market_analyst",
            f"Analyze market size for: {topic}\n\nUse context from research and competitor analysis.",
            allowed_tools=["WebSearch"],
        )

        # Phase 4: Resource Discovery
        log("[4/9] Discovering resources and assessing feasibility...")
        results.resource_findings = await self._run_agent(
            "resource_scout",
            f"Find resources and assess technical feasibility for: {topic}",
            allowed_tools=["WebSearch"],
        )

        # Phase 5: Hypothesis & MVP (Lean Startup)
        log("[5/9] Extracting assumptions and defining MVP...")
        results.hypothesis = await self._run_agent(
            "hypothesis_architect",
            f"Extract riskiest assumptions and define MVP for: {topic}\n\nUse all prior analysis as context.",
            allowed_tools=[],
        )

        # Phase 6: Customer Discovery (Mom Test)
        log("[6/9] Planning customer discovery interviews...")
        results.customer_discovery = await self._run_agent(
            "customer_discovery",
            f"Plan customer discovery for: {topic}\n\nUse hypothesis and prior research as context.",
            allowed_tools=[],
        )

        # Phase 7: Scoring
        log("[7/9] Scoring opportunity across 8 criteria...")
        results.scores = await self._run_agent(
            "scoring_evaluator",
            f"Score the startup opportunity: {topic}\n\n"
            f"Elimination threshold: {self.state.threshold}\n\n"
            "Use all prior analysis to justify scores.",
            allowed_tools=[],
        )

        results.total_score = self._extract_score(results.scores)
        results.eliminated = self._is_eliminated(results.scores)
        results.scoring_iterations = 1

        # Self-evaluation loop for borderline scores (4.5-5.5)
        if 4.5 <= results.total_score <= 5.5 and results.scoring_iterations < 2:
            log("[7b/9] Borderline score detected, re-evaluating...")
            results.scores = await self._run_agent(
                "scoring_evaluator",
                f"Re-evaluate the scoring for: {topic}\n\n"
                f"Previous score was {results.total_score}/10 (borderline).\n"
                f"Threshold: {self.state.threshold}\n\n"
                "Please reconsider each criterion carefully and provide final scores.",
                allowed_tools=[],
            )
            results.total_score = self._extract_score(results.scores)
            results.eliminated = self._is_eliminated(results.scores)
            results.scoring_iterations = 2

        # Phase 8: Pivot Suggestions (only if eliminated)
        if results.eliminated:
            log("[8/9] Generating pivot suggestions for eliminated idea...")
            results.pivot_suggestions = await self._run_agent(
                "pivot_advisor",
                f"Suggest pivots for the eliminated idea: {topic}\n\n"
                f"Score: {results.total_score}/10\n"
                f"Use the scoring weaknesses to inform pivot suggestions.",
                allowed_tools=[],
            )
        else:
            log("[8/9] Skipping pivots (idea passed evaluation)")
            results.pivot_suggestions = "N/A - Idea passed evaluation"

        # Phase 9: Report Generation
        log("[9/9] Generating final evaluation report...")
        results.report = await self._run_agent(
            "report_generator",
            f"Generate the final evaluation report for: {topic}\n\n"
            f"Decision: {'ELIMINATED' if results.eliminated else 'PASSED'}\n"
            f"Score: {results.total_score}/10\n"
            f"Threshold: {self.state.threshold}\n\n"
            "Compile all analysis into a comprehensive report.",
            allowed_tools=[],
        )

        results.decision = "ELIMINATED" if results.eliminated else "PASSED"

        return results


async def evaluate_idea(
    topic: str,
    threshold: float = 5.0,
    verbose: bool = True,
) -> IdeaResult:
    """Convenience function to evaluate a single idea.

    Args:
        topic: The startup idea to evaluate
        threshold: Elimination threshold (default 5.0)
        verbose: Whether to print progress

    Returns:
        IdeaResult with complete evaluation
    """
    orchestrator = IdeationOrchestrator(topic=topic, threshold=threshold)
    return await orchestrator.run_pipeline(verbose=verbose)


async def evaluate_ideas(
    topics: list[str],
    threshold: float = 5.0,
    verbose: bool = True,
) -> list[IdeaResult]:
    """Evaluate multiple ideas sequentially.

    Args:
        topics: List of startup ideas to evaluate
        threshold: Elimination threshold
        verbose: Whether to print progress

    Returns:
        List of IdeaResult for each topic
    """
    results = []
    for i, topic in enumerate(topics, 1):
        if verbose:
            print(f"\n{'='*60}")
            print(f"Evaluating idea {i}/{len(topics)}: {topic}")
            print("=" * 60)

        result = await evaluate_idea(topic, threshold, verbose)
        results.append(result)

        if verbose:
            status = "ELIMINATED" if result.eliminated else "PASSED"
            print(f"\nResult: {status} (Score: {result.total_score}/10)")

    return results
