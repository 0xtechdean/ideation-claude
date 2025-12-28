"""Monitoring and visibility module for the ideation pipeline."""

import json
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

try:
    from rich.console import Console
    from rich.live import Live
    from rich.progress import (
        BarColumn,
        Progress,
        SpinnerColumn,
        TextColumn,
        TimeElapsedColumn,
        TimeRemainingColumn,
    )
    from rich.table import Table
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    Console = None
    Live = None
    Progress = None
    Table = None


class Phase(Enum):
    """Pipeline phases."""

    RESEARCH = "research"
    COMPETITOR_ANALYSIS = "competitor_analysis"
    MARKET_SIZING = "market_sizing"
    RESOURCE_SCOUT = "resource_scout"
    HYPOTHESIS = "hypothesis"
    CUSTOMER_DISCOVERY = "customer_discovery"
    SCORING = "scoring"
    PIVOT = "pivot"
    REPORT = "report"
    COMPLETE = "complete"


class Status(Enum):
    """Status of a phase or operation."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PhaseMetrics:
    """Metrics for a single phase."""

    phase: Phase
    status: Status = Status.PENDING
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    duration: Optional[float] = None
    api_calls: int = 0
    tokens_used: Optional[int] = None
    error: Optional[str] = None
    task_id: Optional[int] = None  # For rich progress tracking

    def start(self):
        """Mark phase as started."""
        self.status = Status.RUNNING
        self.start_time = time.time()

    def complete(self, api_calls: int = 0, tokens_used: Optional[int] = None):
        """Mark phase as completed."""
        self.status = Status.COMPLETED
        self.end_time = time.time()
        if self.start_time:
            self.duration = self.end_time - self.start_time
        self.api_calls = api_calls
        self.tokens_used = tokens_used

    def fail(self, error: str):
        """Mark phase as failed."""
        self.status = Status.FAILED
        self.end_time = time.time()
        if self.start_time:
            self.duration = self.end_time - self.start_time
        self.error = error

    def skip(self):
        """Mark phase as skipped."""
        self.status = Status.SKIPPED


@dataclass
class EvaluationMetrics:
    """Overall metrics for an evaluation."""

    topic: str
    threshold: float
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    total_duration: Optional[float] = None
    phases: dict[str, PhaseMetrics] = field(default_factory=dict)
    total_api_calls: int = 0
    total_tokens_used: Optional[int] = None
    final_score: Optional[float] = None
    eliminated: bool = False
    orchestrator_mode: str = "direct"  # "direct" or "subagent"

    def add_phase(self, phase: Phase, metrics: PhaseMetrics):
        """Add phase metrics."""
        self.phases[phase.value] = metrics

    def complete(self, final_score: float, eliminated: bool):
        """Mark evaluation as complete."""
        self.end_time = time.time()
        self.total_duration = self.end_time - self.start_time
        self.final_score = final_score
        self.eliminated = eliminated
        self.total_api_calls = sum(p.api_calls for p in self.phases.values())
        self.total_tokens_used = sum(
            p.tokens_used for p in self.phases.values() if p.tokens_used
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "topic": self.topic,
            "threshold": self.threshold,
            "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
            "end_time": (
                datetime.fromtimestamp(self.end_time).isoformat()
                if self.end_time
                else None
            ),
            "total_duration": self.total_duration,
            "final_score": self.final_score,
            "eliminated": self.eliminated,
            "orchestrator_mode": self.orchestrator_mode,
            "total_api_calls": self.total_api_calls,
            "total_tokens_used": self.total_tokens_used,
            "phases": {
                phase: {
                    "status": metrics.status.value,
                    "duration": metrics.duration,
                    "api_calls": metrics.api_calls,
                    "tokens_used": metrics.tokens_used,
                    "error": metrics.error,
                }
                for phase, metrics in self.phases.items()
            },
        }

    def save_json(self, path: Path):
        """Save metrics to JSON file."""
        path.write_text(json.dumps(self.to_dict(), indent=2))


class PipelineMonitor:
    """Monitor for tracking pipeline execution."""

    def __init__(
        self,
        topic: str,
        threshold: float,
        verbose: bool = True,
        orchestrator_mode: str = "direct",
        output_dir: Optional[Path] = None,
    ):
        """Initialize the monitor.

        Args:
            topic: The startup idea being evaluated
            threshold: Elimination threshold
            verbose: Whether to show progress output
            orchestrator_mode: "direct" or "subagent"
            output_dir: Directory to save metrics JSON files
        """
        self.metrics = EvaluationMetrics(
            topic=topic, threshold=threshold, orchestrator_mode=orchestrator_mode
        )
        self.verbose = verbose
        self.output_dir = output_dir or Path(".")
        self.console = Console() if RICH_AVAILABLE else None
        self.progress = None
        self.live = None

        if verbose and RICH_AVAILABLE:
            self.progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
                TimeRemainingColumn(),
                console=self.console,
            )
        elif verbose:
            # Fallback to simple print-based logging
            print(f"\n[Monitoring] Starting evaluation: {topic}")
            print(f"[Monitoring] Threshold: {threshold}")
            print(f"[Monitoring] Mode: {orchestrator_mode}\n")

    def start_phase(self, phase: Phase, description: str = None):
        """Start tracking a phase."""
        metrics = PhaseMetrics(phase=phase)
        metrics.start()
        self.metrics.add_phase(phase, metrics)

        if self.verbose:
            phase_name = phase.value.replace("_", " ").title()
            desc = description or f"Running {phase_name}..."
            if self.progress:
                task_id = self.progress.add_task(desc, total=100)
                metrics.task_id = task_id
            elif not RICH_AVAILABLE:
                print(f"[Phase] {phase_name}: Starting...")

        return metrics

    def update_phase(self, phase: Phase, progress: float = None, message: str = None):
        """Update phase progress."""
        phase_key = phase.value
        if phase_key in self.metrics.phases:
            metrics = self.metrics.phases[phase_key]
            if self.verbose:
                if self.progress and hasattr(metrics, "task_id"):
                    if progress is not None:
                        self.progress.update(metrics.task_id, completed=progress)
                    if message:
                        self.progress.update(
                            metrics.task_id, description=f"{message}..."
                        )
                elif not RICH_AVAILABLE and message:
                    print(f"[Phase] {phase.value}: {message}")

    def complete_phase(
        self, phase: Phase, api_calls: int = 0, tokens_used: Optional[int] = None
    ):
        """Mark a phase as completed."""
        phase_key = phase.value
        if phase_key in self.metrics.phases:
            metrics = self.metrics.phases[phase_key]
            metrics.complete(api_calls=api_calls, tokens_used=tokens_used)

            if self.verbose:
                if self.progress and hasattr(metrics, "task_id"):
                    self.progress.update(metrics.task_id, completed=100)
                elif not RICH_AVAILABLE:
                    phase_name = phase.value.replace("_", " ").title()
                    duration_str = f" ({metrics.duration:.2f}s)" if metrics.duration else ""
                    print(f"[Phase] {phase_name}: Completed{duration_str}")

    def fail_phase(self, phase: Phase, error: str):
        """Mark a phase as failed."""
        phase_key = phase.value
        if phase_key in self.metrics.phases:
            metrics = self.metrics.phases[phase_key]
            metrics.fail(error)

    def skip_phase(self, phase: Phase):
        """Mark a phase as skipped."""
        phase_key = phase.value
        if phase_key in self.metrics.phases:
            metrics = self.metrics.phases[phase_key]
            metrics.skip()

    def complete_evaluation(self, final_score: float, eliminated: bool):
        """Mark evaluation as complete."""
        self.metrics.complete(final_score, eliminated)

        # Save metrics to JSON
        metrics_file = (
            self.output_dir
            / "metrics"
            / f"{self.metrics.topic.replace(' ', '_').lower()}_metrics.json"
        )
        metrics_file.parent.mkdir(parents=True, exist_ok=True)
        self.metrics.save_json(metrics_file)

        if self.verbose:
            if RICH_AVAILABLE:
                self._print_summary()
            else:
                self._print_simple_summary()

    def _print_summary(self):
        """Print evaluation summary table."""
        table = Table(title="Evaluation Metrics", show_header=True, header_style="bold")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Topic", self.metrics.topic)
        table.add_row("Threshold", str(self.metrics.threshold))
        table.add_row("Final Score", f"{self.metrics.final_score:.2f}/10")
        table.add_row("Status", "ELIMINATED" if self.metrics.eliminated else "PASSED")
        table.add_row(
            "Total Duration", f"{self.metrics.total_duration:.2f}s"
            if self.metrics.total_duration
            else "N/A"
        )
        table.add_row("Total API Calls", str(self.metrics.total_api_calls))
        if self.metrics.total_tokens_used:
            table.add_row("Total Tokens", str(self.metrics.total_tokens_used))

        self.console.print("\n")
        self.console.print(table)

        # Phase breakdown
        phase_table = Table(title="Phase Breakdown", show_header=True)
        phase_table.add_column("Phase", style="cyan")
        phase_table.add_column("Status", style="green")
        phase_table.add_column("Duration", style="yellow")
        phase_table.add_column("API Calls", style="blue")

        for phase_name, metrics in self.metrics.phases.items():
            phase_table.add_row(
                phase_name.replace("_", " ").title(),
                metrics.status.value.upper(),
                f"{metrics.duration:.2f}s" if metrics.duration else "N/A",
                str(metrics.api_calls),
            )

        self.console.print("\n")
        self.console.print(phase_table)

    def _print_simple_summary(self):
        """Print simple text-based summary."""
        print("\n" + "=" * 60)
        print("EVALUATION METRICS")
        print("=" * 60)
        print(f"Topic: {self.metrics.topic}")
        print(f"Threshold: {self.metrics.threshold}")
        print(f"Final Score: {self.metrics.final_score:.2f}/10")
        print(f"Status: {'ELIMINATED' if self.metrics.eliminated else 'PASSED'}")
        if self.metrics.total_duration:
            print(f"Total Duration: {self.metrics.total_duration:.2f}s")
        print(f"Total API Calls: {self.metrics.total_api_calls}")
        if self.metrics.total_tokens_used:
            print(f"Total Tokens: {self.metrics.total_tokens_used}")
        
        print("\nPhase Breakdown:")
        for phase_name, metrics in self.metrics.phases.items():
            status = metrics.status.value.upper()
            duration = f"{metrics.duration:.2f}s" if metrics.duration else "N/A"
            print(f"  - {phase_name.replace('_', ' ').title()}: {status} ({duration})")

    def __enter__(self):
        """Context manager entry."""
        if self.verbose and RICH_AVAILABLE and self.progress:
            self.live = Live(self.progress, console=self.console, refresh_per_second=10)
            self.live.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.live:
            self.live.__exit__(exc_type, exc_val, exc_tb)

