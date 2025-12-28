"""Pytest configuration and fixtures."""

import os
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test_anthropic_key")
    monkeypatch.setenv("MEM0_API_KEY", "")
    monkeypatch.setenv("OPENAI_API_KEY", "test_openai_key")
    monkeypatch.setenv("MEM0_USER_ID", "test_user")


@pytest.fixture
def mock_claude_query():
    """Mock Claude query function."""
    with patch("ideation_claude.orchestrator.query") as mock:
        # Create a mock async generator
        async def mock_generator():
            mock_message = MagicMock()
            mock_message.content = "Test response"
            mock_message.session_id = "test_session_123"
            yield mock_message

        mock.return_value = mock_generator()
        yield mock


@pytest.fixture
def mock_memory():
    """Mock Mem0 memory instance."""
    with patch("ideation_claude.memory.Memory") as mock_memory_class, \
         patch("ideation_claude.memory.MemoryClient") as mock_client_class:
        
        mock_instance = MagicMock()
        mock_instance.add.return_value = {"id": "test_memory_id"}
        mock_instance.get_all.return_value = {"results": []}
        mock_instance.search.return_value = {"results": []}
        
        # Return mock instance for both classes
        mock_memory_class.from_config.return_value = mock_instance
        mock_client_class.return_value = mock_instance
        
        yield mock_instance


@pytest.fixture
def sample_idea_result():
    """Sample IdeaResult for testing."""
    from ideation_claude.orchestrator import IdeaResult
    
    return IdeaResult(
        topic="Test Startup Idea",
        research_insights="Test research insights",
        competitor_analysis="Test competitor analysis",
        market_sizing="Test market sizing",
        total_score=6.5,
        eliminated=False,
    )


@pytest.fixture
def sample_pipeline_state():
    """Sample PipelineState for testing."""
    from ideation_claude.orchestrator import PipelineState
    
    return PipelineState(
        topic="Test Startup Idea",
        threshold=5.0,
    )

