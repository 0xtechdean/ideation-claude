"""CLI interface for Ideation-Claude Orchestrator.

This is the central orchestrator that coordinates 9 specialized agent repositories
via webhook triggers (repository_dispatch) and Mem0 for shared context.
"""

import asyncio
import sys
from pathlib import Path

import click
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

from .memory import get_memory
from .orchestrator_webhook import evaluate_with_webhooks


@click.group(invoke_without_command=True, context_settings={'help_option_names': ['-h', '--help']})
@click.option(
    "--threshold",
    "-t",
    default=5.0,
    type=float,
    help="Elimination threshold (1-10, default: 5.0)",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Save report to file",
)
@click.option(
    "--quiet",
    "-q",
    is_flag=True,
    help="Suppress progress output",
)
@click.option(
    "--problem-only",
    "-p",
    is_flag=True,
    help="Only run problem validation phase (focus on validating the problem)",
)
@click.pass_context
def cli(ctx, threshold, output, quiet, problem_only):
    """Ideation-Claude Orchestrator: Multi-agent problem validator.

    Coordinates 9 specialized agents via webhook triggers to evaluate startup problems:
    - Problem validation (research, market analysis, customer discovery)
    - Solution validation (competitive analysis, feasibility, MVP definition)
    - Scoring and recommendations

    Examples:

        # Evaluate a problem
        ideation-claude "Legal research is too time-consuming and expensive"

        # With custom threshold
        ideation-claude --threshold 6.0 "Your problem"

        # Problem validation only
        ideation-claude --problem-only "Your problem"
    """
    # Get topics from remaining args
    topics = []
    if ctx.invoked_subcommand is None:
        remaining_args = getattr(ctx, 'args', [])
        if not remaining_args:
            known_commands = {'add', 'pending', 'search', 'list', 'similar', 'insights'}
            skip_next = False
            for arg in sys.argv[1:]:
                if skip_next:
                    skip_next = False
                    continue
                if arg.startswith('-'):
                    if arg in ['-t', '--threshold', '-o', '--output']:
                        skip_next = True
                    continue
                if arg not in known_commands:
                    topics.append(arg)
        else:
            topics = remaining_args

    if topics:
        run_evaluation(list(topics), threshold, output, not quiet, problem_only)
    elif ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


def run_evaluation(
    problems: list[str],
    threshold: float,
    output: str | None,
    verbose: bool,
    problem_only: bool = False,
):
    """Run the evaluation pipeline using webhook-triggered agents."""
    results = []
    for problem in problems:
        result = evaluate_with_webhooks(
            problem,
            threshold=threshold,
            problem_only=problem_only,
            verbose=verbose,
        )
        results.append(result)

    # Print summary
    click.echo("\n" + "=" * 60)
    click.echo("EVALUATION SUMMARY")
    click.echo("=" * 60)

    passed = [r for r in results if not r.eliminated]
    eliminated = [r for r in results if r.eliminated]

    click.echo(f"\nTotal problems evaluated: {len(results)}")
    click.echo(f"Passed: {len(passed)}")
    click.echo(f"Eliminated: {len(eliminated)}")
    click.echo(f"Threshold: {threshold}")

    if passed:
        click.echo("\nPASSED PROBLEMS:")
        for r in sorted(passed, key=lambda x: x.score, reverse=True):
            click.echo(f"  - {r.problem[:50]}...: {r.score}/10")

    if eliminated:
        click.echo("\nELIMINATED PROBLEMS:")
        for r in sorted(eliminated, key=lambda x: x.score, reverse=True):
            click.echo(f"  - {r.problem[:50]}...: {r.score}/10")

    # Save report if requested
    if output:
        report_content = "\n\n---\n\n".join(r.report for r in results)
        Path(output).write_text(report_content)
        click.echo(f"\nReport saved to: {output}")


@cli.command()
@click.argument("problem")
def add(problem):
    """Add a pending problem to Mem0 for later evaluation."""
    memory = get_memory()
    memory_id = memory.save_pending_idea(problem)
    if memory_id != "unknown":
        click.echo(f"Added pending problem: {problem}")
        click.echo(f"  Memory ID: {memory_id[:8]}...")
    else:
        click.echo(f"Failed to add problem: {problem}")


@cli.command()
@click.option("--limit", "-l", default=50, help="Maximum number of results")
def pending(limit):
    """List all pending problems from Mem0."""
    memory = get_memory()
    ideas = memory.get_pending_ideas(limit=limit)
    if not ideas:
        click.echo("No pending problems found.")
        return

    click.echo(f"Found {len(ideas)} pending problem(s):")
    for i, idea in enumerate(ideas, 1):
        meta = idea.get("metadata", {})
        topic = meta.get("topic", "Unknown")
        timestamp = meta.get("timestamp", "N/A")
        click.echo(f"  {i}. {topic}")
        click.echo(f"     Added: {timestamp}")


@cli.command()
@click.argument("query")
@click.option("--limit", "-l", default=5, help="Maximum number of results")
def search(query, limit):
    """Search memory for similar problems and insights."""
    memory = get_memory()
    results = memory.search_similar_ideas(query, limit=limit)

    if not results:
        click.echo(f"No similar problems found for: {query}")
        return

    click.echo(f"\nFound {len(results)} similar problems:\n")
    for i, result in enumerate(results, 1):
        meta = result.get("metadata", {})
        topic = meta.get("topic", "Unknown")
        status = meta.get("status", "unknown").upper()
        score = meta.get("score", 0.0)
        click.echo(f"{i}. {topic}")
        click.echo(f"   Status: {status}, Score: {score}/10")
        click.echo()


@cli.command()
@click.option("--status", "-s", type=click.Choice(["passed", "eliminated", "all"]), default="all", help="Filter by status")
@click.option("--limit", "-l", default=20, help="Maximum number of problems to show")
def list(status, limit):
    """List all evaluated problems from memory."""
    memory = get_memory()
    status_filter = None if status == "all" else status
    ideas = memory.get_all_ideas(status=status_filter, limit=limit)

    if not ideas:
        click.echo("No problems found in memory.")
        return

    click.echo(f"\nFound {len(ideas)} problems:\n")
    for i, idea in enumerate(ideas, 1):
        meta = idea.get("metadata", {})
        topic = meta.get("topic", "Unknown")
        idea_status = meta.get("status", "unknown").upper()
        score = meta.get("score", 0.0)
        timestamp = meta.get("timestamp", "Unknown")
        click.echo(f"{i}. {topic}")
        click.echo(f"   Status: {idea_status}, Score: {score}/10")
        click.echo(f"   Date: {timestamp}")
        click.echo()


@cli.command()
@click.argument("topic")
def similar(topic):
    """Check if a similar problem was previously evaluated."""
    memory = get_memory()
    similar_idea = memory.check_if_similar_eliminated(topic)

    if similar_idea:
        meta = similar_idea.get("metadata", {})
        click.echo(f"\nFound similar problem: {meta.get('topic', 'Unknown')}")
        click.echo(f"   Status: {meta.get('status', 'unknown').upper()}")
        click.echo(f"   Score: {meta.get('score', 0.0)}/10")
        click.echo(f"   Date: {meta.get('timestamp', 'Unknown')}")
    else:
        click.echo(f"\nNo similar eliminated problems found for: {topic}")


@cli.command()
@click.argument("query")
@click.option("--limit", "-l", default=5, help="Maximum number of insights")
def insights(query, limit):
    """Get market insights from past evaluations."""
    memory = get_memory()
    insights_list = memory.get_market_insights(query, limit=limit)

    if not insights_list:
        click.echo(f"No insights found for: {query}")
        return

    click.echo(f"\nFound {len(insights_list)} market insights:\n")
    for i, insight in enumerate(insights_list, 1):
        meta = insight.get("metadata", {})
        phase = meta.get("phase", "unknown")
        topic = meta.get("topic", "Unknown")
        click.echo(f"{i}. [{phase.upper()}] {topic}")
        click.echo()


def main():
    """Entry point for the CLI."""
    try:
        cli(standalone_mode=False)
    except (click.ClickException, SystemExit, Exception) as e:
        if isinstance(e, SystemExit) and e.code == 0:
            raise
        _handle_as_evaluation()


def _handle_as_evaluation():
    """Handle command line arguments as evaluation when command matching fails."""
    known_commands = {'add', 'pending', 'search', 'list', 'similar', 'insights'}
    topics = []
    skip_next = False
    for arg in sys.argv[1:]:
        if skip_next:
            skip_next = False
            continue
        if arg.startswith('-'):
            if arg in ['-t', '--threshold', '-o', '--output', '-l', '--limit']:
                skip_next = True
            continue
        if arg in known_commands:
            return
        topics.append(arg)

    if topics:
        threshold = 5.0
        output = None
        quiet = False
        problem_only = False

        i = 0
        while i < len(sys.argv) - 1:
            arg = sys.argv[i + 1]
            if arg == '--threshold' or arg == '-t':
                if i + 2 < len(sys.argv):
                    threshold = float(sys.argv[i + 2])
                    i += 2
                    continue
            elif arg == '--output' or arg == '-o':
                if i + 2 < len(sys.argv):
                    output = sys.argv[i + 2]
                    i += 2
                    continue
            elif arg == '--quiet' or arg == '-q':
                quiet = True
            elif arg == '--problem-only' or arg == '-p':
                problem_only = True
            i += 1

        run_evaluation(topics, threshold, output, not quiet, problem_only)


if __name__ == "__main__":
    main()
