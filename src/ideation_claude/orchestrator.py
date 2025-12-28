"""Orchestrator for running the ideation pipeline using Claude CLI instances."""

import asyncio
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from claude_code_sdk import query, ClaudeCodeOptions

from .memory import get_memory


@dataclass
class ProblemValidationResult:
    """Result of problem validation phase."""
    
    research_insights: str = ""
    market_sizing: str = ""
    customer_discovery: str = ""
    problem_score: float = 0.0
    problem_validated: bool = False
    problem_eliminated: bool = False
    problem_scoring_text: str = ""


@dataclass
class SolutionValidationResult:
    """Result of solution validation phase."""
    
    competitor_analysis: str = ""
    resource_findings: str = ""
    hypothesis: str = ""
    solution_score: float = 0.0
    solution_validated: bool = False
    solution_eliminated: bool = False
    solution_scoring_text: str = ""


@dataclass
class IdeaResult:
    """Result of evaluating a single startup idea."""

    topic: str
    # Problem validation results
    problem_validation: ProblemValidationResult = field(default_factory=ProblemValidationResult)
    # Solution validation results
    solution_validation: SolutionValidationResult = field(default_factory=SolutionValidationResult)
    # Legacy fields (for backward compatibility)
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

    problem: str
    threshold: float = 5.0
    session_id: Optional[str] = None
    results: IdeaResult = field(default_factory=lambda: IdeaResult(topic=""))

    def __post_init__(self):
        self.results = IdeaResult(topic=self.problem)


class IdeationOrchestrator:
    """Orchestrates the 9-phase startup evaluation pipeline.

    Each agent runs as a Claude CLI instance with session context
    passed between phases for continuity.
    """

    def __init__(self, problem: str, threshold: float = 5.0, use_memory: bool = True):
        """Initialize the orchestrator.

        Args:
            problem: The problem statement to validate and find solutions for
            threshold: Elimination threshold (default 5.0)
            use_memory: Whether to use Mem0 for storing and retrieving context
        """
        self.state = PipelineState(problem=problem, threshold=threshold)
        self.agents_dir = Path(__file__).parent / "agents"
        self.memory = get_memory() if use_memory else None

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

    async def _generate_phase_summary(
        self,
        phase_name: str,
        phase_output: str,
        problem: str,
    ) -> str:
        """Generate a concise summary of what happened in a phase.

        Args:
            phase_name: Name of the phase (e.g., "research", "market_sizing")
            phase_output: The full output from the phase
            problem: The problem statement being evaluated

        Returns:
            A concise summary of the phase
        """
        summary_prompt = f"""Generate a concise summary (2-3 sentences) of what was discovered in the {phase_name} phase for this problem: {problem}

Phase Output:
{phase_output[:3000]}

Provide a brief summary focusing on:
- Key findings
- Important insights
- Critical information discovered

Keep it concise and actionable."""
        
        try:
            summary = await self._run_agent(
                "report_generator",  # Use report generator for summarization
                summary_prompt,
                allowed_tools=[],
            )
            # Extract just the summary text (first few sentences)
            summary_lines = summary.split('\n')[:5]
            return '\n'.join(summary_lines).strip()
        except Exception as e:
            # Fallback to a simple extraction if summarization fails
            return f"Phase {phase_name} completed. Key findings: {phase_output[:500]}..."

    def _extract_score(self, scoring_text: str) -> float:
        """Extract the total score from scoring output."""
        # Look for various patterns the agents might use
        patterns = [
            # Markdown table: | **TOTAL** | **6.25/10** |
            r"\*\*TOTAL\*\*\s*\|\s*\*\*(\d+\.?\d*)/10\*\*",
            # Bold total: **TOTAL**: **6.5/10**
            r"\*\*TOTAL\*\*[:\s]*\*\*(\d+\.?\d*)/10\*\*",
            # Plain: TOTAL: 6.5/10
            r"TOTAL[:\s]*(\d+\.?\d*)/10",
            # Score header: **Score**: 6.25/10
            r"\*\*Score\*\*[:\s]*(\d+\.?\d*)/10",
            # Total Score: 6.5
            r"Total Score[:\s]*(\d+\.?\d*)",
            # Generic: Score: 6.5/10
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

    async def run_problem_validation(
        self, verbose: bool = True, parallel: bool = True, monitor=None
    ) -> ProblemValidationResult:
        """Run problem validation phase - focusing on validating the problem.
        
        This phase validates:
        - Market trends and customer pain points
        - Market size (TAM/SAM/SOM)
        - Customer discovery and validation
        
        Args:
            verbose: Whether to print progress messages
            parallel: Whether to run independent agents in parallel
            monitor: Optional PipelineMonitor instance for tracking
            
        Returns:
            ProblemValidationResult with problem validation findings
        """
        from .monitoring import Phase

        problem = self.state.problem
        result = ProblemValidationResult()

        def log(msg: str):
            if verbose and not monitor:
                print(f"  {msg}")

        # Check for similar problems before starting
        similar_context = ""
        if self.memory:
            similar = self.memory.check_if_similar_eliminated(problem)
            if similar:
                log(f"⚠ Found similar eliminated problem: {similar.get('metadata', {}).get('topic', 'Unknown')}")
            similar_context = self.memory.get_similar_ideas_context(problem)
            if similar_context:
                log("📚 Using context from similar past evaluations")

        # Phase 1: Research - Market trends and customer pain points
        if monitor:
            monitor.start_phase(Phase.RESEARCH, "Researching market trends and pain points")
        else:
            log("[1/3] Researching market trends and customer pain points...")
        
        research_prompt = f"Research market trends and customer pain points for this problem: {problem}"
        if similar_context:
            research_prompt += f"\n\n{similar_context}"
        
        result.research_insights = await self._run_agent(
            "researcher",
            research_prompt,
            allowed_tools=["WebSearch"],
        )
        
        # Store research insights in memory
        if self.memory:
            self.memory.save_phase_output(problem, "research", result.research_insights)
            # Generate and save phase summary
            research_summary = await self._generate_phase_summary("research", result.research_insights, problem)
            self.memory.save_phase_summary(problem, "research", research_summary)
            if verbose and not monitor:
                log(f"📝 Research summary: {research_summary[:150]}...")
        
        if monitor:
            monitor.complete_phase(Phase.RESEARCH, api_calls=1)

        # Phase 2: Market Sizing (TAM/SAM/SOM)
        if monitor:
            monitor.start_phase(Phase.MARKET_SIZING, "Estimating market size")
        else:
            log("[2/3] Estimating market size (TAM/SAM/SOM)...")
        
        result.market_sizing = await self._run_agent(
            "market_analyst",
            f"Analyze market size for this problem: {problem}\n\nResearch context:\n{result.research_insights[:2000]}",
            allowed_tools=["WebSearch"],
        )
        
        if self.memory:
            self.memory.save_phase_output(problem, "market_sizing", result.market_sizing)
            # Generate and save phase summary
            market_summary = await self._generate_phase_summary("market_sizing", result.market_sizing, problem)
            self.memory.save_phase_summary(problem, "market_sizing", market_summary)
            if verbose and not monitor:
                log(f"📝 Market sizing summary: {market_summary[:150]}...")
        
        if monitor:
            monitor.complete_phase(Phase.MARKET_SIZING, api_calls=1)

        # Phase 3: Customer Discovery (Mom Test)
        if monitor:
            monitor.start_phase(Phase.CUSTOMER_DISCOVERY, "Planning customer discovery")
        else:
            log("[3/3] Planning customer discovery interviews (Mom Test)...")
        
        customer_prompt = f"Plan customer discovery interviews for this problem: {problem}\n\n"
        customer_prompt += f"Research Insights:\n{result.research_insights[:1500]}\n\n"
        customer_prompt += f"Market Sizing:\n{result.market_sizing[:1500]}"
        
        result.customer_discovery = await self._run_agent(
            "customer_discovery",
            customer_prompt,
            allowed_tools=[],
        )
        
        if self.memory:
            self.memory.save_phase_output(problem, "customer_discovery", result.customer_discovery)
            # Generate and save phase summary
            customer_summary = await self._generate_phase_summary("customer_discovery", result.customer_discovery, problem)
            self.memory.save_phase_summary(problem, "customer_discovery", customer_summary)
            if verbose and not monitor:
                log(f"📝 Customer discovery summary: {customer_summary[:150]}...")
        
        if monitor:
            monitor.complete_phase(Phase.CUSTOMER_DISCOVERY, api_calls=1)

        # Phase 4: Problem Validation Scoring
        if monitor:
            monitor.start_phase(Phase.SCORING, "Scoring problem validation")
        else:
            log("[4/4] Scoring problem validation...")
        
        problem_context = f"""
Problem Statement: {problem}

Research Insights (Market Trends & Pain Points):
{result.research_insights[:2000]}

Market Sizing (TAM/SAM/SOM):
{result.market_sizing[:2000]}

Customer Discovery Plan:
{result.customer_discovery[:1500]}
"""
        
        problem_scoring_prompt = f"""Score the PROBLEM VALIDATION for this problem: {problem}

Focus on validating the PROBLEM, not the solution. Evaluate:
1. **Problem Clarity** (1-10): How clearly defined is the problem? Is it a real pain point?
2. **Market Need** (1-10): How strong is the market demand for solving this problem?
3. **Market Size** (1-10): What is the addressable market size (TAM/SAM/SOM)?
4. **Customer Validation** (1-10): How testable/validatable is the problem with customers?
5. **Problem Urgency** (1-10): How urgent is solving this problem for customers?
6. **Problem Frequency** (1-10): How often do customers encounter this problem?
7. **Problem Severity** (1-10): How severe is the pain when customers face this problem?
8. **Evidence Quality** (1-10): What evidence exists that this is a real problem?

Elimination threshold: {self.state.threshold}

{problem_context}

Provide a detailed scoring with justification for each criterion, then calculate the average.
If the average score < {self.state.threshold}, mark as ELIMINATED.
"""
        
        result.problem_scoring_text = await self._run_agent(
            "scoring_evaluator",
            problem_scoring_prompt,
            allowed_tools=[],
        )
        
        result.problem_score = self._extract_score(result.problem_scoring_text)
        result.problem_eliminated = self._is_eliminated(result.problem_scoring_text)
        result.problem_validated = not result.problem_eliminated
        
        if monitor:
            monitor.complete_phase(Phase.SCORING, api_calls=1)
        
        if verbose:
            status = "ELIMINATED" if result.problem_eliminated else "VALIDATED"
            log(f"\nProblem Validation Result: {status} (Score: {result.problem_score}/10)")

        return result

    async def run_pipeline(
        self, 
        verbose: bool = True, 
        parallel: bool = True, 
        monitor=None,
        problem_only: bool = False
    ) -> IdeaResult:
        """Run the evaluation pipeline with split problem/solution validation.

        Args:
            verbose: Whether to print progress messages
            parallel: Whether to run independent agents in parallel (default: True)
            monitor: Optional PipelineMonitor instance for tracking
            problem_only: If True, only run problem validation phase

        Returns:
            IdeaResult with all findings
        """
        from .monitoring import Phase

        topic = self.state.topic
        results = self.state.results

        def log(msg: str):
            if verbose and not monitor:
                print(f"  {msg}")

        # Run Problem Validation first (focus on problem)
        log("\n" + "="*60)
        log("PROBLEM VALIDATION PHASE")
        log("="*60)
        
        problem_result = await self.run_problem_validation(verbose, parallel, monitor)
        results.problem_validation = problem_result
        
        # Populate legacy fields for backward compatibility
        results.research_insights = problem_result.research_insights
        results.market_sizing = problem_result.market_sizing
        results.customer_discovery = problem_result.customer_discovery
        
        # If problem validation failed, we can stop early
        if problem_result.problem_eliminated:
            log("\n⚠️  Problem validation failed - problem not validated")
            results.eliminated = True
            results.decision = "ELIMINATED (Problem Not Validated)"
            results.total_score = problem_result.problem_score
            
            # Still generate a report for eliminated ideas
            if not problem_only:
                log("\n[Final] Generating report...")
                results.report = await self._run_agent(
                    "report_generator",
                    f"Generate problem validation report for: {topic}\n\n"
                    f"Decision: ELIMINATED (Problem Not Validated)\n"
                    f"Problem Score: {problem_result.problem_score}/10\n"
                    f"Threshold: {self.state.threshold}\n\n"
                    f"Problem Validation Results:\n{problem_result.problem_scoring_text[:2000]}",
                    allowed_tools=[],
                )
            
            # Save to memory
            if self.memory:
                self.memory.save_idea(
                    topic=problem,
                    eliminated=True,
                    score=problem_result.problem_score,
                    threshold=self.state.threshold,
                    reason=problem_result.problem_scoring_text,
                    research_insights=problem_result.research_insights,
                    market_sizing=problem_result.market_sizing,
                    customer_discovery=problem_result.customer_discovery,
                )
            
            return results
        
        # Problem validated - proceed to solution validation (if not problem_only)
        if problem_only:
            log("\n✅ Problem validated! Use --full-validation to continue with solution validation.")
            results.eliminated = False
            results.decision = "PASSED (Problem Validated)"
            results.total_score = problem_result.problem_score
            return results
        
        log("\n" + "="*60)
        log("SOLUTION VALIDATION PHASE")
        log("="*60)
        
        # Now run solution validation
        # Use problem validation results as context
        solution_result = SolutionValidationResult()
        
        # Phase 1: Competitor Analysis
        if monitor:
            monitor.start_phase(Phase.COMPETITOR_ANALYSIS, "Analyzing competitors")
        else:
            log("[1/4] Analyzing competitive landscape...")
        
        solution_result.competitor_analysis = await self._run_agent(
            "competitor_analyst",
            f"Analyze existing solutions and competitors for this problem: {problem}\n\nProblem Context:\n{problem_result.research_insights[:2000]}",
            allowed_tools=["WebSearch"],
        )
        
        if self.memory:
            self.memory.save_phase_output(problem, "competitor_analysis", solution_result.competitor_analysis)
            # Generate and save phase summary
            competitor_summary = await self._generate_phase_summary("competitor_analysis", solution_result.competitor_analysis, problem)
            self.memory.save_phase_summary(problem, "competitor_analysis", competitor_summary)
            if verbose and not monitor:
                log(f"📝 Competitor analysis summary: {competitor_summary[:150]}...")
        
        if monitor:
            monitor.complete_phase(Phase.COMPETITOR_ANALYSIS, api_calls=1)

        # Phase 2: Resource Findings & Technical Feasibility
        if monitor:
            monitor.start_phase(Phase.RESOURCE_SCOUT, "Assessing technical feasibility")
        else:
            log("[2/4] Discovering resources and assessing technical feasibility...")
        
        solution_result.resource_findings = await self._run_agent(
            "resource_scout",
            f"Find resources and assess technical feasibility for solving this problem: {problem}\n\n"
            f"Problem Context:\n{problem_result.research_insights[:2000]}\n\n"
            f"Competitor Analysis:\n{solution_result.competitor_analysis[:1500]}",
            allowed_tools=["WebSearch"],
        )
        
        if self.memory:
            self.memory.save_phase_output(problem, "resource_findings", solution_result.resource_findings)
            # Generate and save phase summary
            resource_summary = await self._generate_phase_summary("resource_findings", solution_result.resource_findings, problem)
            self.memory.save_phase_summary(problem, "resource_findings", resource_summary)
            if verbose and not monitor:
                log(f"📝 Resource findings summary: {resource_summary[:150]}...")
        
        if monitor:
            monitor.complete_phase(Phase.RESOURCE_SCOUT, api_calls=1)

        # Phase 3: Hypothesis & MVP (Lean Startup)
        if monitor:
            monitor.start_phase(Phase.HYPOTHESIS, "Defining MVP and assumptions")
        else:
            log("[3/4] Extracting assumptions and defining MVP...")
        
        solution_context = f"""
Problem Validation:
- Research Insights: {problem_result.research_insights[:1500]}
- Market Sizing: {problem_result.market_sizing[:1500]}
- Customer Discovery: {problem_result.customer_discovery[:1000]}

Solution Context:
- Competitor Analysis: {solution_result.competitor_analysis[:1500]}
- Resources & Feasibility: {solution_result.resource_findings[:1500]}
"""
        
        solution_result.hypothesis = await self._run_agent(
            "hypothesis_architect",
            f"Extract riskiest assumptions and define MVP for solving this problem: {problem}\n\n{solution_context}",
            allowed_tools=[],
        )
        
        if self.memory:
            self.memory.save_phase_output(problem, "hypothesis", solution_result.hypothesis)
            # Generate and save phase summary
            hypothesis_summary = await self._generate_phase_summary("hypothesis", solution_result.hypothesis, problem)
            self.memory.save_phase_summary(problem, "hypothesis", hypothesis_summary)
            if verbose and not monitor:
                log(f"📝 Hypothesis summary: {hypothesis_summary[:150]}...")
        
        if monitor:
            monitor.complete_phase(Phase.HYPOTHESIS, api_calls=1)

        # Phase 4: Solution Validation Scoring
        if monitor:
            monitor.start_phase(Phase.SCORING, "Scoring solution validation")
        else:
            log("[4/4] Scoring solution validation...")
        
        full_solution_context = f"""
Problem Validation (Score: {problem_result.problem_score}/10):
- Research Insights: {problem_result.research_insights[:2000]}
- Market Sizing: {problem_result.market_sizing[:2000]}
- Customer Discovery: {problem_result.customer_discovery[:1500]}

Solution Validation:
- Competitor Analysis: {solution_result.competitor_analysis[:2000]}
- Resources & Feasibility: {solution_result.resource_findings[:2000]}
- Hypothesis & MVP: {solution_result.hypothesis[:1500]}
"""
        
        solution_scoring_prompt = f"""Score the SOLUTION VALIDATION for solving this problem: {problem}

Focus on validating the SOLUTION, not just the problem. Evaluate:
1. **Solution Fit** (1-10): How well does the solution address the validated problem?
2. **Competitive Advantage** (1-10): How differentiated is this solution from competitors?
3. **Technical Feasibility** (1-10): How feasible is building this solution?
4. **Resource Availability** (1-10): What resources/tools/APIs are available to build this?
5. **MVP Clarity** (1-10): How clear and testable is the MVP?
6. **Assumption Testability** (1-10): How easy/cheap is it to test key assumptions?
7. **Solution Timing** (1-10): Is the timing right for this solution?
8. **Solution Scalability** (1-10): Can this solution scale effectively?

Problem Validation Score: {problem_result.problem_score}/10
Elimination threshold: {self.state.threshold}

{full_solution_context}

Provide a detailed scoring with justification for each criterion, then calculate the average.
If the average score < {self.state.threshold}, mark as ELIMINATED.
"""
        
        solution_result.solution_scoring_text = await self._run_agent(
            "scoring_evaluator",
            solution_scoring_prompt,
            allowed_tools=[],
        )
        
        solution_result.solution_score = self._extract_score(solution_result.solution_scoring_text)
        solution_result.solution_eliminated = self._is_eliminated(solution_result.solution_scoring_text)
        solution_result.solution_validated = not solution_result.solution_eliminated
        
        # Generate and save solution validation summary
        if self.memory:
            solution_validation_summary = f"Solution validation completed. Score: {solution_result.solution_score}/10. Status: {'VALIDATED' if solution_result.solution_validated else 'ELIMINATED'}. Key findings from competitor analysis, resource assessment, and hypothesis definition."
            self.memory.save_phase_summary(problem, "solution_validation", solution_validation_summary)
            if verbose and not monitor:
                log(f"📝 Solution validation summary saved to memory")
        
        # Combine problem and solution scores (weighted: 60% problem, 40% solution)
        results.total_score = (problem_result.problem_score * 0.6) + (solution_result.solution_score * 0.4)
        results.eliminated = problem_result.problem_eliminated or solution_result.solution_eliminated
        
        # Store solution validation results
        results.solution_validation = solution_result
        
        # Populate legacy fields
        results.competitor_analysis = solution_result.competitor_analysis
        results.resource_findings = solution_result.resource_findings
        results.hypothesis = solution_result.hypothesis
        results.scores = f"Problem Score: {problem_result.problem_score}/10\nSolution Score: {solution_result.solution_score}/10\nCombined Score: {results.total_score}/10\n\nProblem Validation:\n{problem_result.problem_scoring_text[:1500]}\n\nSolution Validation:\n{solution_result.solution_scoring_text[:1500]}"
        
        if monitor:
            monitor.complete_phase(Phase.SCORING, api_calls=1)

        # Phase 5: Pivot (if eliminated) + Report
        if results.eliminated:
            log("[5/5] Generating pivot suggestions and final report...")
            # Run pivot and report in parallel since they're independent
            if parallel:
                pivot_task = self._run_agent(
                    "pivot_advisor",
                    f"Suggest alternative approaches for solving this problem: {problem}\n\n"
                    f"Score: {results.total_score}/10\n"
                    f"Scoring details:\n{results.scores[:1500]}",
                    allowed_tools=[],
                )
                report_task = self._run_agent(
                    "report_generator",
                    f"Generate the final evaluation report for this problem: {problem}\n\n"
                    f"Decision: ELIMINATED\n"
                    f"Problem Score: {problem_result.problem_score}/10\n"
                    f"Solution Score: {solution_result.solution_score}/10\n"
                    f"Combined Score: {results.total_score}/10\n"
                    f"Threshold: {self.state.threshold}\n\n{full_solution_context}",
                    allowed_tools=[],
                )
                results.pivot_suggestions, results.report = await asyncio.gather(
                    pivot_task, report_task
                )
            else:
                results.pivot_suggestions = await self._run_agent(
                    "pivot_advisor",
                    f"Suggest alternative approaches for solving this problem: {problem}\n\n"
                    f"Score: {results.total_score}/10\n"
                    f"Scoring details:\n{results.scores[:1500]}",
                    allowed_tools=[],
                )
                results.report = await self._run_agent(
                    "report_generator",
                    f"Generate the final evaluation report for this problem: {problem}\n\n"
                    f"Decision: ELIMINATED\n"
                    f"Problem Score: {problem_result.problem_score}/10\n"
                    f"Solution Score: {solution_result.solution_score}/10\n"
                    f"Combined Score: {results.total_score}/10\n"
                    f"Threshold: {self.state.threshold}\n\n{full_solution_context}",
                    allowed_tools=[],
                )
        else:
            log("[5/5] Generating final report (passed evaluation)...")
            results.pivot_suggestions = "N/A - Idea passed evaluation"
            results.report = await self._run_agent(
                "report_generator",
                f"Generate the final evaluation report for this problem: {problem}\n\n"
                f"Decision: PASSED\n"
                f"Problem Score: {problem_result.problem_score}/10\n"
                f"Solution Score: {solution_result.solution_score}/10\n"
                f"Combined Score: {results.total_score}/10\n"
                f"Threshold: {self.state.threshold}\n\n{full_solution_context}",
                allowed_tools=[],
            )

        results.decision = "ELIMINATED" if results.eliminated else "PASSED"

        # Save complete problem evaluation to memory
        if self.memory:
            self.memory.save_idea(
                topic=problem,
                eliminated=results.eliminated,
                score=results.total_score,
                threshold=self.state.threshold,
                reason=results.scores if results.eliminated else "",
                research_insights=problem_result.research_insights,
                competitor_analysis=solution_result.competitor_analysis,
                market_sizing=problem_result.market_sizing,
                resource_findings=solution_result.resource_findings,
                hypothesis=solution_result.hypothesis,
                customer_discovery=problem_result.customer_discovery,
                pivot_suggestions=results.pivot_suggestions if results.eliminated else "",
            )
            log(f"💾 Saved evaluation to memory (status: {results.decision})")

        return results


async def evaluate_idea(
    problem: str,
    threshold: float = 5.0,
    verbose: bool = True,
    monitor=None,
    use_memory: bool = True,
    problem_only: bool = False,
) -> IdeaResult:
    """Convenience function to evaluate a problem and find solutions.

    Args:
        problem: The problem statement to validate and find solutions for
        threshold: Elimination threshold (default 5.0)
        verbose: Whether to print progress
        monitor: Optional PipelineMonitor instance
        use_memory: Whether to use Mem0 for storing and retrieving context
        problem_only: If True, only run problem validation phase

    Returns:
        IdeaResult with complete evaluation
    """
    orchestrator = IdeationOrchestrator(problem=problem, threshold=threshold, use_memory=use_memory)
    return await orchestrator.run_pipeline(verbose=verbose, monitor=monitor, problem_only=problem_only)


async def evaluate_ideas(
    problems: list[str],
    threshold: float = 5.0,
    verbose: bool = True,
) -> list[IdeaResult]:
    """Evaluate multiple problems sequentially.

    Args:
        problems: List of problem statements to evaluate
        threshold: Elimination threshold
        verbose: Whether to print progress

    Returns:
        List of IdeaResult for each problem
    """
    results = []
    for i, problem in enumerate(problems, 1):
        if verbose:
            print(f"\n{'='*60}")
            print(f"Evaluating problem {i}/{len(problems)}: {problem}")
            print("=" * 60)

        result = await evaluate_idea(problem, threshold, verbose)
        results.append(result)

        if verbose:
            status = "ELIMINATED" if result.eliminated else "PASSED"
            print(f"\nResult: {status} (Score: {result.total_score}/10)")

    return results
