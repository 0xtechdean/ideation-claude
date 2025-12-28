"""CLI interface for Ideation-Claude."""

import asyncio
from pathlib import Path

import click

from .orchestrator import evaluate_idea, evaluate_ideas


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
@click.pass_context
def cli(ctx, topics, threshold, output, interactive, quiet):
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
        asyncio.run(interactive_mode(threshold, quiet))
    elif topics:
        asyncio.run(run_evaluation(list(topics), threshold, output, not quiet))
    elif ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


async def run_evaluation(
    topics: list[str],
    threshold: float,
    output: str | None,
    verbose: bool,
):
    """Run the evaluation pipeline."""
    if len(topics) == 1:
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


async def interactive_mode(threshold: float, quiet: bool):
    """Run in interactive mode."""
    topics: list[str] = []

    click.echo("Ideation-Claude Interactive Mode")
    click.echo("=" * 40)
    click.echo("Commands:")
    click.echo("  add <idea>  - Add an idea to evaluate")
    click.echo("  list        - Show current ideas")
    click.echo("  clear       - Clear all ideas")
    click.echo("  run         - Run evaluation on all ideas")
    click.echo("  threshold   - Set elimination threshold")
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
            click.echo("Commands: add, list, clear, run, threshold, help, quit")

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
                await run_evaluation(topics, threshold, None, not quiet)
                topics.clear()

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


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
