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

    async def run_pipeline(self, verbose: bool = True, parallel: bool = True) -> IdeaResult:
        """Run the full 9-phase evaluation pipeline.

        Args:
            verbose: Whether to print progress messages
            parallel: Whether to run independent agents in parallel (default: True)

        Returns:
            IdeaResult with all findings
        """
        topic = self.state.topic
        results = self.state.results

        def log(msg: str):
            if verbose:
                print(f"  {msg}")

        # Phase 1: Research (must run first - baseline for all others)
        log("[1/6] Researching market trends and pain points...")
        results.research_insights = await self._run_agent(
            "researcher",
            f"Research market trends and customer pain points for: {topic}",
            allowed_tools=["WebSearch"],
        )

        # Phase 2: Parallel analysis (Competitor + Market + Resource)
        # All three only need research context, so they can run simultaneously
        if parallel:
            log("[2/6] Running parallel analysis (competitor, market, resources)...")
            competitor_task = self._run_agent(
                "competitor_analyst",
                f"Analyze competitors for: {topic}\n\nResearch context:\n{results.research_insights[:2000]}",
                allowed_tools=["WebSearch"],
            )
            market_task = self._run_agent(
                "market_analyst",
                f"Analyze market size for: {topic}\n\nResearch context:\n{results.research_insights[:2000]}",
                allowed_tools=["WebSearch"],
            )
            resource_task = self._run_agent(
                "resource_scout",
                f"Find resources and assess technical feasibility for: {topic}\n\nResearch context:\n{results.research_insights[:2000]}",
                allowed_tools=["WebSearch"],
            )

            # Run all three in parallel
            competitor_result, market_result, resource_result = await asyncio.gather(
                competitor_task, market_task, resource_task
            )
            results.competitor_analysis = competitor_result
            results.market_sizing = market_result
            results.resource_findings = resource_result
        else:
            # Sequential fallback
            log("[2/6] Analyzing competitive landscape...")
            results.competitor_analysis = await self._run_agent(
                "competitor_analyst",
                f"Analyze competitors for: {topic}\n\nResearch context:\n{results.research_insights[:2000]}",
                allowed_tools=["WebSearch"],
            )

            log("[3/6] Estimating market size (TAM/SAM/SOM)...")
            results.market_sizing = await self._run_agent(
                "market_analyst",
                f"Analyze market size for: {topic}\n\nResearch context:\n{results.research_insights[:2000]}",
                allowed_tools=["WebSearch"],
            )

            log("[4/6] Discovering resources and assessing feasibility...")
            results.resource_findings = await self._run_agent(
                "resource_scout",
                f"Find resources and assess technical feasibility for: {topic}\n\nResearch context:\n{results.research_insights[:2000]}",
                allowed_tools=["WebSearch"],
            )

        # Build context summary for subsequent phases
        context_summary = f"""
Research Insights:
{results.research_insights[:1500]}

Competitor Analysis:
{results.competitor_analysis[:1500]}

Market Sizing:
{results.market_sizing[:1500]}

Resources & Feasibility:
{results.resource_findings[:1500]}
"""

        # Phase 3: Hypothesis & MVP (Lean Startup)
        log("[3/6] Extracting assumptions and defining MVP...")
        results.hypothesis = await self._run_agent(
            "hypothesis_architect",
            f"Extract riskiest assumptions and define MVP for: {topic}\n\n{context_summary}",
            allowed_tools=[],
        )

        # Phase 4: Customer Discovery (Mom Test)
        log("[4/6] Planning customer discovery interviews...")
        results.customer_discovery = await self._run_agent(
            "customer_discovery",
            f"Plan customer discovery for: {topic}\n\nHypothesis:\n{results.hypothesis[:1500]}\n\n{context_summary}",
            allowed_tools=[],
        )

        # Phase 5: Scoring
        log("[5/6] Scoring opportunity across 8 criteria...")
        full_context = f"""
{context_summary}

Hypothesis & MVP:
{results.hypothesis[:1000]}

Customer Discovery Plan:
{results.customer_discovery[:1000]}
"""
        results.scores = await self._run_agent(
            "scoring_evaluator",
            f"Score the startup opportunity: {topic}\n\n"
            f"Elimination threshold: {self.state.threshold}\n\n{full_context}",
            allowed_tools=[],
        )

        results.total_score = self._extract_score(results.scores)
        results.eliminated = self._is_eliminated(results.scores)
        results.scoring_iterations = 1

        # Self-evaluation loop for borderline scores (4.5-5.5)
        if 4.5 <= results.total_score <= 5.5 and results.scoring_iterations < 2:
            log("[5b/6] Borderline score detected, re-evaluating...")
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

        # Phase 6: Pivot (if eliminated) + Report
        if results.eliminated:
            log("[6/6] Generating pivot suggestions and final report...")
            # Run pivot and report in parallel since they're independent
            if parallel:
                pivot_task = self._run_agent(
                    "pivot_advisor",
                    f"Suggest pivots for the eliminated idea: {topic}\n\n"
                    f"Score: {results.total_score}/10\n"
                    f"Scoring details:\n{results.scores[:1500]}",
                    allowed_tools=[],
                )
                report_task = self._run_agent(
                    "report_generator",
                    f"Generate the final evaluation report for: {topic}\n\n"
                    f"Decision: ELIMINATED\n"
                    f"Score: {results.total_score}/10\n"
                    f"Threshold: {self.state.threshold}\n\n{full_context}",
                    allowed_tools=[],
                )
                results.pivot_suggestions, results.report = await asyncio.gather(
                    pivot_task, report_task
                )
            else:
                results.pivot_suggestions = await self._run_agent(
                    "pivot_advisor",
                    f"Suggest pivots for the eliminated idea: {topic}\n\n"
                    f"Score: {results.total_score}/10\n"
                    f"Scoring details:\n{results.scores[:1500]}",
                    allowed_tools=[],
                )
                results.report = await self._run_agent(
                    "report_generator",
                    f"Generate the final evaluation report for: {topic}\n\n"
                    f"Decision: ELIMINATED\n"
                    f"Score: {results.total_score}/10\n"
                    f"Threshold: {self.state.threshold}\n\n{full_context}",
                    allowed_tools=[],
                )
        else:
            log("[6/6] Generating final report (passed evaluation)...")
            results.pivot_suggestions = "N/A - Idea passed evaluation"
            results.report = await self._run_agent(
                "report_generator",
                f"Generate the final evaluation report for: {topic}\n\n"
                f"Decision: PASSED\n"
                f"Score: {results.total_score}/10\n"
                f"Threshold: {self.state.threshold}\n\n{full_context}",
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
