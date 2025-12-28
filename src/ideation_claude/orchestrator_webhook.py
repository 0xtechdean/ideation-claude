"""Webhook-based orchestrator that invokes agents via GitHub repository_dispatch.

This orchestrator triggers individual agent repos via webhook and uses Mem0
for context sharing between agents.
"""

import json
import os
import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import requests
from rich.console import Console

from .memory import IdeaMemory

console = Console()

# Agent repos in execution order
PROBLEM_VALIDATION_AGENTS = [
    "researcher",
    "market-analyst",
    "customer-discovery",
]

SOLUTION_VALIDATION_AGENTS = [
    "competitor-analyst",
    "resource-scout",
    "hypothesis-architect",
]

COMPLETION_AGENTS = [
    "pivot-advisor",
    "report-generator",
]

SCORING_AGENT = "scoring-evaluator"

GITHUB_ORG = "Othentic-Ai"


@dataclass
class WebhookOrchestratorResult:
    """Result from webhook orchestrator evaluation."""
    session_id: str
    problem: str
    score: float
    eliminated: bool
    report: str
    phases_completed: list[str]


class WebhookOrchestrator:
    """Orchestrator that invokes agents via GitHub repository_dispatch webhooks."""

    def __init__(
        self,
        github_token: str = None,
        mem0_api_key: str = None,
        threshold: float = 5.0,
        problem_only: bool = False,
        verbose: bool = False,
    ):
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self.mem0_api_key = mem0_api_key or os.getenv("MEM0_API_KEY")
        self.threshold = threshold
        self.problem_only = problem_only
        self.verbose = verbose
        self.memory = IdeaMemory()

        if not self.github_token:
            raise ValueError("GITHUB_TOKEN environment variable is required")

    def _trigger_agent(self, agent_name: str, session_id: str, problem: str) -> bool:
        """Trigger an agent repo via repository_dispatch.

        Args:
            agent_name: Name of the agent (e.g., "researcher")
            session_id: Session ID for context
            problem: Problem statement

        Returns:
            True if trigger was successful
        """
        repo_name = f"ideation-agent-{agent_name}"
        url = f"https://api.github.com/repos/{GITHUB_ORG}/{repo_name}/dispatches"

        headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json",
        }

        payload = {
            "event_type": "run",
            "client_payload": {
                "session_id": session_id,
                "problem": problem,
            }
        }

        if self.verbose:
            console.print(f"[dim]Triggering {repo_name}...[/dim]")

        try:
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 204:
                console.print(f"[green]Triggered {agent_name} agent[/green]")
                return True
            else:
                console.print(f"[red]Failed to trigger {agent_name}: {response.status_code}[/red]")
                return False
        except Exception as e:
            console.print(f"[red]Error triggering {agent_name}: {e}[/red]")
            return False

    def _wait_for_phase(
        self,
        phase: str,
        session_id: str,
        timeout: int = 300,
        poll_interval: int = 10
    ) -> Optional[dict]:
        """Wait for a phase to complete by polling Mem0.

        Args:
            phase: Phase name to wait for
            session_id: Session ID
            timeout: Maximum wait time in seconds
            poll_interval: Time between polls in seconds

        Returns:
            Phase output dict or None if timeout
        """
        user_id = f"ideation_session_{session_id}"
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                # Search for phase completion in Mem0
                from mem0 import MemoryClient
                client = MemoryClient(api_key=self.mem0_api_key)

                results = client.search(
                    f"phase {phase} session {session_id} status complete",
                    user_id=user_id,
                    limit=1,
                )

                if results.get("results"):
                    result = results["results"][0]
                    if self.verbose:
                        console.print(f"[green]Phase {phase} completed[/green]")
                    return result

            except Exception as e:
                if self.verbose:
                    console.print(f"[dim]Waiting for {phase}... ({e})[/dim]")

            time.sleep(poll_interval)

        console.print(f"[yellow]Timeout waiting for {phase}[/yellow]")
        return None

    def _create_session(self, session_id: str, problem: str) -> None:
        """Create a new session in Mem0.

        Args:
            session_id: Session ID
            problem: Problem statement
        """
        from mem0 import MemoryClient
        client = MemoryClient(api_key=self.mem0_api_key)
        user_id = f"ideation_session_{session_id}"

        session_data = {
            "session_id": session_id,
            "problem": problem,
            "threshold": self.threshold,
            "created_at": datetime.now().isoformat(),
            "status": "started",
        }

        client.add(
            json.dumps(session_data),
            user_id=user_id,
            metadata={
                "type": "session",
                "session_id": session_id,
            }
        )

    def evaluate(self, problem: str) -> WebhookOrchestratorResult:
        """Evaluate a problem using webhook-triggered agents.

        Args:
            problem: Problem statement to evaluate

        Returns:
            WebhookOrchestratorResult with evaluation results
        """
        session_id = str(uuid.uuid4())[:8]
        phases_completed = []

        console.print(f"\n[bold blue]Starting evaluation[/bold blue]")
        console.print(f"Session ID: {session_id}")
        console.print(f"Problem: {problem[:100]}...")
        console.print(f"Threshold: {self.threshold}")

        # Create session in Mem0
        self._create_session(session_id, problem)

        # Phase 1: Problem Validation
        console.print("\n[bold]Phase 1: Problem Validation[/bold]")

        for agent in PROBLEM_VALIDATION_AGENTS:
            if self._trigger_agent(agent, session_id, problem):
                result = self._wait_for_phase(agent.replace("-", "_"), session_id)
                if result:
                    phases_completed.append(agent)

        # Trigger scoring for problem phase
        if self._trigger_agent(SCORING_AGENT, session_id, problem):
            score_result = self._wait_for_phase("scoring_evaluator", session_id)
            if score_result:
                phases_completed.append("scoring-evaluator-problem")

        # Check if eliminated at problem phase
        # (In real implementation, parse score from Mem0)
        problem_score = 6.0  # Placeholder - would parse from Mem0

        if problem_score < self.threshold:
            console.print(f"\n[red]ELIMINATED at problem phase (score: {problem_score})[/red]")

            # Trigger pivot advisor
            if self._trigger_agent("pivot-advisor", session_id, problem):
                self._wait_for_phase("pivot_advisor", session_id)
                phases_completed.append("pivot-advisor")

            # Trigger report generator
            if self._trigger_agent("report-generator", session_id, problem):
                self._wait_for_phase("report_generator", session_id)
                phases_completed.append("report-generator")

            return WebhookOrchestratorResult(
                session_id=session_id,
                problem=problem,
                score=problem_score,
                eliminated=True,
                report="See Mem0 for full report",
                phases_completed=phases_completed,
            )

        if self.problem_only:
            return WebhookOrchestratorResult(
                session_id=session_id,
                problem=problem,
                score=problem_score,
                eliminated=False,
                report="Problem validation only",
                phases_completed=phases_completed,
            )

        # Phase 2: Solution Validation
        console.print("\n[bold]Phase 2: Solution Validation[/bold]")

        for agent in SOLUTION_VALIDATION_AGENTS:
            if self._trigger_agent(agent, session_id, problem):
                result = self._wait_for_phase(agent.replace("-", "_"), session_id)
                if result:
                    phases_completed.append(agent)

        # Trigger final scoring
        if self._trigger_agent(SCORING_AGENT, session_id, problem):
            score_result = self._wait_for_phase("scoring_evaluator", session_id)
            if score_result:
                phases_completed.append("scoring-evaluator-solution")

        # Calculate combined score
        solution_score = 7.0  # Placeholder - would parse from Mem0
        combined_score = (problem_score * 0.6) + (solution_score * 0.4)

        if combined_score < self.threshold:
            console.print(f"\n[red]ELIMINATED at solution phase (score: {combined_score})[/red]")
            eliminated = True

            # Trigger pivot advisor
            if self._trigger_agent("pivot-advisor", session_id, problem):
                self._wait_for_phase("pivot_advisor", session_id)
                phases_completed.append("pivot-advisor")
        else:
            console.print(f"\n[green]PASSED (score: {combined_score})[/green]")
            eliminated = False

        # Trigger report generator
        if self._trigger_agent("report-generator", session_id, problem):
            self._wait_for_phase("report_generator", session_id)
            phases_completed.append("report-generator")

        return WebhookOrchestratorResult(
            session_id=session_id,
            problem=problem,
            score=combined_score,
            eliminated=eliminated,
            report="See Mem0 for full report",
            phases_completed=phases_completed,
        )


def evaluate_with_webhooks(
    problem: str,
    threshold: float = 5.0,
    problem_only: bool = False,
    verbose: bool = False,
) -> WebhookOrchestratorResult:
    """Evaluate a problem using webhook-triggered agents.

    Args:
        problem: Problem statement to evaluate
        threshold: Elimination threshold (default 5.0)
        problem_only: If True, only run problem validation phase
        verbose: If True, show detailed progress

    Returns:
        WebhookOrchestratorResult with evaluation results
    """
    orchestrator = WebhookOrchestrator(
        threshold=threshold,
        problem_only=problem_only,
        verbose=verbose,
    )
    return orchestrator.evaluate(problem)
