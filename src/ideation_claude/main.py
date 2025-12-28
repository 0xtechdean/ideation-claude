"""CLI interface for Ideation-Claude."""

import asyncio
from pathlib import Path

import click
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

from .memory import get_memory
from .orchestrator import evaluate_idea, evaluate_ideas
from .orchestrator_subagent import evaluate_with_subagents


@click.group(invoke_without_command=True)
@click.argument("topics", nargs=-1)
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
    "--interactive",
    "-i",
    is_flag=True,
    help="Run in interactive mode",
)
@click.option(
    "--quiet",
    "-q",
    is_flag=True,
    help="Suppress progress output",
)
@click.option(
    "--subagent",
    "-s",
    is_flag=True,
    help="Use sub-agent orchestrator (single coordinator spawns sub-agents)",
)
@click.option(
    "--metrics",
    "-m",
    is_flag=True,
    help="Save detailed metrics to JSON file",
)
@click.pass_context
def cli(ctx, topics, threshold, output, interactive, quiet, subagent, metrics):
    """Ideation-Claude: Multi-agent startup idea validator.

    Evaluate startup ideas using Claude CLI agents that perform:
    - Market research and trend analysis
    - Competitive landscape analysis
    - TAM/SAM/SOM market sizing
    - Technical feasibility assessment
    - Lean Startup hypothesis extraction
    - Mom Test customer discovery planning
    - 8-criteria scoring
    - Pivot suggestions for eliminated ideas

    Examples:

        # Evaluate a single idea
        ideation-claude "AI-powered legal research assistant"

        # Evaluate multiple ideas
        ideation-claude "Legal AI" "Sustainable packaging"

        # With custom threshold
        ideation-claude --threshold 6.0 "Your idea"

        # Interactive mode
        ideation-claude --interactive
    """
    if interactive:
        asyncio.run(interactive_mode(threshold, quiet, subagent))
    elif topics:
        asyncio.run(run_evaluation(list(topics), threshold, output, not quiet, subagent, metrics))
    elif ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


async def run_evaluation(
    topics: list[str],
    threshold: float,
    output: str | None,
    verbose: bool,
    subagent: bool = False,
    metrics: bool = False,
):
    """Run the evaluation pipeline."""
    from .monitoring import PipelineMonitor
    
    if subagent:
        # Use sub-agent orchestrator (single coordinator spawns sub-agents)
        if verbose:
            click.echo("Using sub-agent orchestrator mode...")
        results = []
        for topic in topics:
            if metrics:
                with PipelineMonitor(topic, threshold, verbose, "subagent") as monitor:
                    result = await evaluate_with_subagents(topic, threshold, verbose)
                    monitor.complete_evaluation(result.total_score, result.eliminated)
            else:
                result = await evaluate_with_subagents(topic, threshold, verbose)
            results.append(result)
    elif len(topics) == 1:
        if metrics:
            with PipelineMonitor(topics[0], threshold, verbose, "direct") as monitor:
                result = await evaluate_idea(topics[0], threshold, verbose, monitor=monitor)
                monitor.complete_evaluation(result.total_score, result.eliminated)
        else:
            result = await evaluate_idea(topics[0], threshold, verbose)
        results = [result]
    else:
        results = await evaluate_ideas(topics, threshold, verbose)

    # Print summary
    click.echo("\n" + "=" * 60)
    click.echo("EVALUATION SUMMARY")
    click.echo("=" * 60)

    passed = [r for r in results if not r.eliminated]
    eliminated = [r for r in results if r.eliminated]

    click.echo(f"\nTotal ideas evaluated: {len(results)}")
    click.echo(f"Passed: {len(passed)}")
    click.echo(f"Eliminated: {len(eliminated)}")
    click.echo(f"Threshold: {threshold}")

    if passed:
        click.echo("\nPASSED IDEAS:")
        for r in sorted(passed, key=lambda x: x.total_score, reverse=True):
            click.echo(f"  - {r.topic}: {r.total_score}/10")

    if eliminated:
        click.echo("\nELIMINATED IDEAS:")
        for r in sorted(eliminated, key=lambda x: x.total_score, reverse=True):
            click.echo(f"  - {r.topic}: {r.total_score}/10")

    # Save report if requested
    if output:
        report_content = "\n\n---\n\n".join(r.report for r in results)
        Path(output).write_text(report_content)
        click.echo(f"\nReport saved to: {output}")


async def interactive_mode(threshold: float, quiet: bool, subagent: bool = False):
    """Run in interactive mode."""
    topics: list[str] = []

    click.echo("Ideation-Claude Interactive Mode")
    if subagent:
        click.echo("(Sub-agent orchestrator mode)")
    click.echo("=" * 40)
    click.echo("Commands:")
    click.echo("  add <idea>  - Add an idea to evaluate")
    click.echo("  list        - Show current ideas")
    click.echo("  clear       - Clear all ideas")
    click.echo("  run         - Run evaluation on all ideas")
    click.echo("  threshold   - Set elimination threshold")
    click.echo("  mode        - Toggle sub-agent mode")
    click.echo("  help        - Show this help")
    click.echo("  quit        - Exit")
    click.echo()

    while True:
        try:
            command = click.prompt("ideation", type=str).strip()
        except (EOFError, KeyboardInterrupt):
            click.echo("\nGoodbye!")
            break

        if not command:
            continue

        parts = command.split(maxsplit=1)
        cmd = parts[0].lower()

        if cmd == "quit" or cmd == "exit" or cmd == "q":
            click.echo("Goodbye!")
            break

        elif cmd == "help" or cmd == "h":
            click.echo("Commands: add, list, clear, run, threshold, mode, help, quit")

        elif cmd == "add" or cmd == "a":
            if len(parts) > 1:
                topic = parts[1]
                topics.append(topic)
                click.echo(f"Added: {topic}")
            else:
                click.echo("Usage: add <idea>")

        elif cmd == "list" or cmd == "l":
            if topics:
                click.echo("Current ideas:")
                for i, topic in enumerate(topics, 1):
                    click.echo(f"  {i}. {topic}")
            else:
                click.echo("No ideas added yet. Use 'add <idea>' to add one.")

        elif cmd == "clear" or cmd == "c":
            topics.clear()
            click.echo("All ideas cleared.")

        elif cmd == "run" or cmd == "r":
            if not topics:
                click.echo("No ideas to evaluate. Use 'add <idea>' first.")
            else:
                await run_evaluation(topics, threshold, None, not quiet, subagent)
                topics.clear()

        elif cmd == "mode" or cmd == "m":
            subagent = not subagent
            mode_name = "sub-agent" if subagent else "direct SDK"
            click.echo(f"Switched to {mode_name} orchestrator mode.")

        elif cmd == "threshold" or cmd == "t":
            if len(parts) > 1:
                try:
                    threshold = float(parts[1])
                    click.echo(f"Threshold set to: {threshold}")
                except ValueError:
                    click.echo("Invalid threshold. Use a number between 1-10.")
            else:
                click.echo(f"Current threshold: {threshold}")

        else:
            # Treat as an idea to add
            topics.append(command)
            click.echo(f"Added: {command}")


@cli.command()
@click.argument("topic")
def add(topic):
    """Add a pending idea to Mem0 for later evaluation."""
    memory = get_memory()
    memory_id = memory.save_pending_idea(topic)
    if memory_id != "unknown":
        click.echo(f"✓ Added pending idea: {topic}")
        click.echo(f"  Memory ID: {memory_id[:8]}...")
    else:
        click.echo(f"✗ Failed to add idea: {topic}")


@cli.command()
@click.option("--limit", "-l", default=50, help="Maximum number of results")
def pending(limit):
    """List all pending ideas from Mem0."""
    memory = get_memory()
    ideas = memory.get_pending_ideas(limit=limit)
    if not ideas:
        click.echo("No pending ideas found.")
        return
    
    click.echo(f"Found {len(ideas)} pending idea(s):")
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
    """Search memory for similar ideas and insights."""
    memory = get_memory()
    results = memory.search_similar_ideas(query, limit=limit)
    
    if not results:
        click.echo(f"No similar ideas found for: {query}")
        return
    
    click.echo(f"\nFound {len(results)} similar ideas:\n")
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
@click.option("--limit", "-l", default=20, help="Maximum number of ideas to show")
def list(status, limit):
    """List all evaluated ideas from memory."""
    memory = get_memory()
    status_filter = None if status == "all" else status
    ideas = memory.get_all_ideas(status=status_filter, limit=limit)
    
    if not ideas:
        click.echo("No ideas found in memory.")
        return
    
    click.echo(f"\nFound {len(ideas)} ideas:\n")
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
    """Check if a similar idea was previously evaluated."""
    memory = get_memory()
    similar_idea = memory.check_if_similar_eliminated(topic)
    
    if similar_idea:
        meta = similar_idea.get("metadata", {})
        click.echo(f"\n⚠ Found similar idea: {meta.get('topic', 'Unknown')}")
        click.echo(f"   Status: {meta.get('status', 'unknown').upper()}")
        click.echo(f"   Score: {meta.get('score', 0.0)}/10")
        click.echo(f"   Date: {meta.get('timestamp', 'Unknown')}")
    else:
        click.echo(f"\n✓ No similar eliminated ideas found for: {topic}")


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
    cli()


if __name__ == "__main__":
    main()
