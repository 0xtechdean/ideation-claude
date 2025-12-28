"""Tests for orchestrator module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from ideation_claude.orchestrator import (
    IdeaResult,
    IdeationOrchestrator,
    PipelineState,
    evaluate_idea,
    evaluate_ideas,
)


class TestIdeaResult:
    """Tests for IdeaResult dataclass."""

    def test_idea_result_creation(self):
        """Test creating an IdeaResult."""
        result = IdeaResult(topic="Test Idea")
        assert result.topic == "Test Idea"
        assert result.total_score == 0.0
        assert result.eliminated is False
        assert result.scoring_iterations == 0

    def test_idea_result_with_values(self):
        """Test IdeaResult with all values."""
        result = IdeaResult(
            topic="Test Idea",
            research_insights="Insights",
            total_score=7.5,
            eliminated=False,
        )
        assert result.topic == "Test Idea"
        assert result.research_insights == "Insights"
        assert result.total_score == 7.5
        assert result.eliminated is False


class TestPipelineState:
    """Tests for PipelineState dataclass."""

    def test_pipeline_state_creation(self):
        """Test creating a PipelineState."""
        state = PipelineState(topic="Test Idea", threshold=6.0)
        assert state.topic == "Test Idea"
        assert state.threshold == 6.0
        assert state.session_id is None
        assert state.results.topic == "Test Idea"

    def test_pipeline_state_default_threshold(self):
        """Test PipelineState with default threshold."""
        state = PipelineState(topic="Test Idea")
        assert state.threshold == 5.0


class TestIdeationOrchestrator:
    """Tests for IdeationOrchestrator class."""

    def test_orchestrator_initialization(self):
        """Test orchestrator initialization."""
        orchestrator = IdeationOrchestrator("Test Idea", threshold=6.0)
        assert orchestrator.state.topic == "Test Idea"
        assert orchestrator.state.threshold == 6.0
        assert orchestrator.agents_dir.exists()

    def test_get_agent_prompt(self):
        """Test loading agent prompts."""
        orchestrator = IdeationOrchestrator("Test Idea")
        prompt = orchestrator._get_agent_prompt("researcher")
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_get_agent_prompt_not_found(self):
        """Test error when agent prompt not found."""
        orchestrator = IdeationOrchestrator("Test Idea")
        with pytest.raises(FileNotFoundError):
            orchestrator._get_agent_prompt("nonexistent_agent")

    def test_extract_score(self):
        """Test score extraction from text."""
        orchestrator = IdeationOrchestrator("Test Idea")
        
        # Test various score patterns
        assert orchestrator._extract_score("**TOTAL**: **6.5/10**") == 6.5
        assert orchestrator._extract_score("TOTAL: 7.0/10") == 7.0
        assert orchestrator._extract_score("Total Score: 8.5") == 8.5
        assert orchestrator._extract_score("Score: 5.0/10") == 5.0
        assert orchestrator._extract_score("No score here") == 0.0

    def test_is_eliminated(self):
        """Test elimination detection."""
        orchestrator = IdeationOrchestrator("Test Idea")
        
        assert orchestrator._is_eliminated("ELIMINATE") is True
        assert orchestrator._is_eliminated("eliminate") is True
        assert orchestrator._is_eliminated("ELIMINATE this idea") is True
        assert orchestrator._is_eliminated("PASS") is False
        assert orchestrator._is_eliminated("") is False

    @pytest.mark.asyncio
    async def test_run_agent(self, mock_claude_query):
        """Test running an agent."""
        orchestrator = IdeationOrchestrator("Test Idea")
        
        result = await orchestrator._run_agent(
            "researcher",
            "Test prompt",
            allowed_tools=["WebSearch"]
        )
        
        assert isinstance(result, str)
        assert "Test response" in result

    @pytest.mark.asyncio
    async def test_run_agent_with_session(self, mock_claude_query):
        """Test running an agent with existing session."""
        orchestrator = IdeationOrchestrator("Test Idea")
        orchestrator.state.session_id = "existing_session"
        
        result = await orchestrator._run_agent("researcher", "Test prompt")
        
        assert isinstance(result, str)
        # Verify session was used (would be checked in actual implementation)


@pytest.mark.asyncio
async def test_evaluate_idea(mock_claude_query, mock_env_vars):
    """Test evaluate_idea function."""
    # This is an integration test that would require mocking the full pipeline
    # For now, we'll just test that it's callable
    with patch("ideation_claude.orchestrator.IdeationOrchestrator") as mock_orch:
        mock_instance = MagicMock()
        mock_result = IdeaResult(topic="Test Idea", total_score=6.0)
        mock_instance.run_pipeline = AsyncMock(return_value=mock_result)
        mock_orch.return_value = mock_instance
        
        result = await evaluate_idea("Test Idea", threshold=5.0, verbose=False, monitor=None)
        
        assert result.topic == "Test Idea"
        assert result.total_score == 6.0


@pytest.mark.asyncio
async def test_evaluate_ideas(mock_claude_query, mock_env_vars):
    """Test evaluate_ideas function."""
    with patch("ideation_claude.orchestrator.IdeationOrchestrator") as mock_orch:
        mock_instance = MagicMock()
        # Return different results for each idea
        mock_results = [
            IdeaResult(topic="Idea 1", total_score=6.0),
            IdeaResult(topic="Idea 2", total_score=7.0),
        ]
        mock_instance.run_pipeline = AsyncMock(side_effect=mock_results)
        mock_orch.return_value = mock_instance
        
        results = await evaluate_ideas(
            ["Idea 1", "Idea 2"],
            threshold=5.0,
            verbose=False
        )
        
        assert len(results) == 2
        topics = [r.topic for r in results]
        assert "Idea 1" in topics
        assert "Idea 2" in topics

