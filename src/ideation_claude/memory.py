"""Memory service for storing eliminated ideas using Mem0."""

import os
from datetime import datetime
from typing import Optional

from mem0 import Memory, MemoryClient


class IdeaMemory:
    """Memory service for storing and retrieving eliminated startup ideas.

    Supports two modes:
    - Cloud mode: Set MEM0_API_KEY env var to use Mem0's managed service
    - Local mode: Falls back to local Qdrant storage if no API key
    """

    def __init__(self, user_id: str = None):
        """Initialize the memory service.

        Args:
            user_id: Unique identifier for the user/session.
                     Defaults to MEM0_USER_ID env var or "ideation_claude"
        """
        self.user_id = user_id or os.getenv("MEM0_USER_ID", "ideation_claude")
        self._memory = None
        self._is_cloud = bool(os.getenv("MEM0_API_KEY"))

    @property
    def memory(self):
        """Lazy initialization of mem0 Memory instance."""
        if self._memory is None:
            mem0_api_key = os.getenv("MEM0_API_KEY")

            if mem0_api_key:
                # Cloud mode: Use Mem0's managed service
                print(f"    [mem0] Using cloud mode with user_id: {self.user_id}")
                self._memory = MemoryClient(api_key=mem0_api_key)
            else:
                # Local mode: Use local Qdrant storage
                print(f"    [mem0] Using local mode with user_id: {self.user_id}")
                config = {
                    "llm": {
                        "provider": "openai",
                        "config": {
                            "model": "gpt-4o-mini",
                            "temperature": 0.1,
                        }
                    },
                    "embedder": {
                        "provider": "openai",
                        "config": {
                            "model": "text-embedding-3-small",
                        }
                    },
                    "vector_store": {
                        "provider": "qdrant",
                        "config": {
                            "collection_name": "eliminated_ideas",
                            "path": "./.mem0_data",
                        }
                    },
                }
                self._memory = Memory.from_config(config)
        return self._memory

    def save_eliminated_idea(
        self,
        topic: str,
        reason: str,
        scores: dict,
        research_insights: str = "",
        competitor_analysis: str = "",
        market_sizing: str = "",
    ) -> str:
        """Save an eliminated idea to memory.

        Args:
            topic: The startup idea/topic that was eliminated
            reason: The reason for elimination
            scores: Scoring breakdown
            research_insights: Research findings
            competitor_analysis: Competitor landscape
            market_sizing: Market size analysis

        Returns:
            Memory ID
        """
        memory_text = f"""
Eliminated Startup Idea: {topic}

Elimination Date: {datetime.now().isoformat()}

Reason for Elimination: {reason}

Scores: {scores}

Research Insights Summary: {research_insights[:500] if research_insights else 'N/A'}

Competitor Landscape: {competitor_analysis[:500] if competitor_analysis else 'N/A'}

Market Size: {market_sizing[:500] if market_sizing else 'N/A'}
"""
        result = self.memory.add(
            memory_text,
            user_id=self.user_id,
            metadata={
                "type": "eliminated_idea",
                "topic": topic,
                "timestamp": datetime.now().isoformat(),
            }
        )
        return result.get("id", "unknown")

    def get_eliminated_ideas(self, limit: int = 50) -> list[dict]:
        """Retrieve all eliminated ideas from memory.

        Args:
            limit: Maximum number of ideas to retrieve

        Returns:
            List of eliminated idea memories
        """
        memories = self.memory.get_all(user_id=self.user_id)
        return [m for m in memories.get("results", [])[:limit]]

    def search_similar_ideas(self, query: str, limit: int = 5) -> list[dict]:
        """Search for similar eliminated ideas.

        Args:
            query: Search query (e.g., a new idea to check against)
            limit: Maximum number of results

        Returns:
            List of similar eliminated ideas
        """
        results = self.memory.search(query, user_id=self.user_id, limit=limit)
        return results.get("results", [])

    def check_if_similar_eliminated(self, topic: str, threshold: float = 0.8) -> Optional[dict]:
        """Check if a similar idea was previously eliminated.

        Args:
            topic: The new idea to check
            threshold: Similarity threshold (0-1)

        Returns:
            The similar eliminated idea if found, None otherwise
        """
        results = self.search_similar_ideas(topic, limit=1)
        if results:
            top_result = results[0]
            return top_result
        return None


# Global memory instance
_memory_instance: Optional[IdeaMemory] = None


def get_memory(user_id: str = None) -> IdeaMemory:
    """Get or create the global memory instance.

    Args:
        user_id: User/session identifier. Defaults to MEM0_USER_ID env var.

    Returns:
        IdeaMemory instance
    """
    global _memory_instance
    if _memory_instance is None:
        _memory_instance = IdeaMemory(user_id=user_id)
    return _memory_instance
