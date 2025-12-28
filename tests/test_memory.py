"""Tests for memory module."""

import os
from unittest.mock import MagicMock, patch

import pytest

from ideation_claude.memory import IdeaMemory, get_memory


class TestIdeaMemory:
    """Tests for IdeaMemory class."""

    def test_memory_initialization_default_user(self, mock_env_vars):
        """Test memory initialization with default user."""
        memory = IdeaMemory()
        assert memory.user_id == "test_user"
        assert memory._is_cloud is False  # No MEM0_API_KEY set

    def test_memory_initialization_custom_user(self, mock_env_vars):
        """Test memory initialization with custom user."""
        memory = IdeaMemory(user_id="custom_user")
        assert memory.user_id == "custom_user"

    def test_memory_initialization_cloud_mode(self, monkeypatch):
        """Test memory initialization in cloud mode."""
        monkeypatch.setenv("MEM0_API_KEY", "test_key")
        memory = IdeaMemory()
        assert memory._is_cloud is True

    def test_memory_lazy_initialization_local(self, mock_env_vars, mock_memory):
        """Test lazy initialization of memory in local mode."""
        memory = IdeaMemory()
        # Accessing the property should initialize it
        mem_instance = memory.memory
        assert mem_instance is not None

    def test_memory_lazy_initialization_cloud(self, monkeypatch, mock_memory):
        """Test lazy initialization of memory in cloud mode."""
        monkeypatch.setenv("MEM0_API_KEY", "test_key")
        memory = IdeaMemory()
        mem_instance = memory.memory
        assert mem_instance is not None

    def test_save_eliminated_idea(self, mock_env_vars, mock_memory):
        """Test saving an eliminated idea."""
        memory = IdeaMemory()
        memory_id = memory.save_eliminated_idea(
            topic="Test Idea",
            reason="Low score",
            scores={"total": 4.0},
            research_insights="Some insights",
            competitor_analysis="Some analysis",
            market_sizing="Some sizing",
        )
        
        assert memory_id == "test_memory_id"
        memory.memory.add.assert_called_once()

    def test_get_eliminated_ideas(self, mock_env_vars, mock_memory):
        """Test retrieving eliminated ideas."""
        memory = IdeaMemory()
        ideas = memory.get_eliminated_ideas(limit=10)
        
        assert isinstance(ideas, list)
        memory.memory.get_all.assert_called_once_with(user_id="test_user")

    def test_search_similar_ideas(self, mock_env_vars, mock_memory):
        """Test searching for similar ideas."""
        memory = IdeaMemory()
        results = memory.search_similar_ideas("test query", limit=5)
        
        assert isinstance(results, list)
        memory.memory.search.assert_called_once_with(
            "test query",
            user_id="test_user",
            limit=5
        )

    def test_check_if_similar_eliminated_found(self, mock_env_vars, mock_memory):
        """Test checking for similar eliminated ideas when found."""
        # Mock a result
        mock_memory.search.return_value = {
            "results": [{"id": "1", "content": "Similar idea"}]
        }
        
        memory = IdeaMemory()
        result = memory.check_if_similar_eliminated("Test Idea")
        
        assert result is not None
        assert result["id"] == "1"

    def test_check_if_similar_eliminated_not_found(self, mock_env_vars, mock_memory):
        """Test checking for similar eliminated ideas when not found."""
        # Mock empty results
        mock_memory.search.return_value = {"results": []}
        
        memory = IdeaMemory()
        result = memory.check_if_similar_eliminated("Test Idea")
        
        assert result is None


class TestGetMemory:
    """Tests for get_memory function."""

    def test_get_memory_creates_instance(self, mock_env_vars):
        """Test that get_memory creates a new instance."""
        # Clear any existing instance
        import ideation_claude.memory
        ideation_claude.memory._memory_instance = None
        
        memory = get_memory()
        assert isinstance(memory, IdeaMemory)

    def test_get_memory_returns_singleton(self, mock_env_vars):
        """Test that get_memory returns the same instance."""
        import ideation_claude.memory
        ideation_claude.memory._memory_instance = None
        
        memory1 = get_memory()
        memory2 = get_memory()
        
        assert memory1 is memory2

    def test_get_memory_with_user_id(self, mock_env_vars):
        """Test get_memory with custom user_id."""
        import ideation_claude.memory
        ideation_claude.memory._memory_instance = None
        
        memory = get_memory(user_id="custom_user")
        assert memory.user_id == "custom_user"

