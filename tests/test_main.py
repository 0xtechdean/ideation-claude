"""Tests for main CLI module."""

import pytest
from unittest.mock import MagicMock, patch
from click.testing import CliRunner

from ideation_claude.main import cli, run_evaluation


class TestCLI:
    """Tests for CLI interface."""

    def test_cli_help(self):
        """Test CLI help output."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Ideation-Claude" in result.output

    def test_cli_no_args_shows_help(self):
        """Test CLI without arguments shows help."""
        runner = CliRunner()
        result = runner.invoke(cli, [])
        assert result.exit_code == 0
        assert "Ideation-Claude" in result.output

    @pytest.mark.asyncio
    async def test_run_evaluation_single_idea(self):
        """Test running evaluation with a single idea."""
        with patch("ideation_claude.main.evaluate_idea") as mock_eval:
            from ideation_claude.orchestrator import IdeaResult
            
            mock_result = IdeaResult(topic="Test Idea", total_score=6.0)
            mock_eval.return_value = mock_result
            
            await run_evaluation(
                topics=["Test Idea"],
                threshold=5.0,
                output=None,
                verbose=False,
                subagent=False,
                metrics=False,
            )
            
            mock_eval.assert_called_once_with("Test Idea", 5.0, False, None)

    @pytest.mark.asyncio
    async def test_run_evaluation_multiple_ideas(self):
        """Test running evaluation with multiple ideas."""
        with patch("ideation_claude.main.evaluate_ideas") as mock_eval:
            from ideation_claude.orchestrator import IdeaResult
            
            mock_results = [
                IdeaResult(topic="Idea 1", total_score=6.0),
                IdeaResult(topic="Idea 2", total_score=7.0),
            ]
            mock_eval.return_value = mock_results
            
            await run_evaluation(
                topics=["Idea 1", "Idea 2"],
                threshold=5.0,
                output=None,
                verbose=False,
                subagent=False,
                metrics=False,
            )
            
            mock_eval.assert_called_once_with(["Idea 1", "Idea 2"], 5.0, False)

    @pytest.mark.asyncio
    async def test_run_evaluation_subagent_mode(self):
        """Test running evaluation in subagent mode."""
        with patch("ideation_claude.main.evaluate_with_subagents") as mock_eval:
            from ideation_claude.orchestrator_subagent import SubAgentResult
            
            mock_result = SubAgentResult(
                topic="Test Idea",
                total_score=6.0,
                eliminated=False
            )
            mock_eval.return_value = mock_result
            
            await run_evaluation(
                topics=["Test Idea"],
                threshold=5.0,
                output=None,
                verbose=False,
                subagent=True,
                metrics=False,
            )
            
            mock_eval.assert_called_once_with("Test Idea", 5.0, False)

    @pytest.mark.asyncio
    async def test_run_evaluation_with_output(self, tmp_path):
        """Test running evaluation with output file."""
        with patch("ideation_claude.main.evaluate_idea") as mock_eval:
            from ideation_claude.orchestrator import IdeaResult
            
            output_file = tmp_path / "report.md"
            mock_result = IdeaResult(
                topic="Test Idea",
                total_score=6.0,
                report="# Test Report\n\nContent here"
            )
            mock_eval.return_value = mock_result
            
            await run_evaluation(
                topics=["Test Idea"],
                threshold=5.0,
                output=str(output_file),
                verbose=False,
                subagent=False,
                metrics=False,
            )
            
            assert output_file.exists()
            assert "Test Report" in output_file.read_text()

