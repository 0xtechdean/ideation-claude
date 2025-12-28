"""Memory service for storing ideas and evaluation data using Mem0."""

import os
from datetime import datetime
from typing import Optional

from mem0 import Memory, MemoryClient


class IdeaMemory:
    """Memory service for storing and retrieving startup ideas and evaluation data.

    Supports two modes:
    - Cloud mode: Set MEM0_API_KEY env var to use Mem0's managed service
    - Local mode: Falls back to local Qdrant storage if no API key
    
    Stores:
    - All evaluated ideas (both passed and eliminated)
    - Phase outputs (research, competitor analysis, market sizing, etc.)
    - Market intelligence and insights
    - Similar ideas and patterns
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

    def save_idea(
        self,
        topic: str,
        eliminated: bool,
        score: float,
        threshold: float,
        reason: str = "",
        research_insights: str = "",
        competitor_analysis: str = "",
        market_sizing: str = "",
        resource_findings: str = "",
        hypothesis: str = "",
        customer_discovery: str = "",
        pivot_suggestions: str = "",
    ) -> str:
        """Save an evaluated idea to memory (both passed and eliminated).

        Args:
            topic: The startup idea/topic
            eliminated: Whether the idea was eliminated
            score: Final score
            threshold: Elimination threshold used
            reason: Reason for elimination (if eliminated)
            research_insights: Research findings
            competitor_analysis: Competitor landscape
            market_sizing: Market size analysis
            resource_findings: Resource and feasibility findings
            hypothesis: Hypothesis and MVP definition
            customer_discovery: Customer discovery plan
            pivot_suggestions: Pivot suggestions (if eliminated)

        Returns:
            Memory ID
        """
        status = "ELIMINATED" if eliminated else "PASSED"
        memory_text = f"""
Startup Idea: {topic}

Status: {status}
Score: {score}/10
Threshold: {threshold}
Date: {datetime.now().isoformat()}

{f'Reason for Elimination: {reason}' if eliminated else 'Idea passed evaluation'}

Research Insights: {research_insights[:1000] if research_insights else 'N/A'}

Competitor Analysis: {competitor_analysis[:1000] if competitor_analysis else 'N/A'}

Market Sizing: {market_sizing[:1000] if market_sizing else 'N/A'}

Resource Findings: {resource_findings[:500] if resource_findings else 'N/A'}

Hypothesis & MVP: {hypothesis[:500] if hypothesis else 'N/A'}

Customer Discovery: {customer_discovery[:500] if customer_discovery else 'N/A'}

{f'Pivot Suggestions: {pivot_suggestions[:500]}' if pivot_suggestions and eliminated else ''}
"""
        result = self.memory.add(
            memory_text,
            user_id=self.user_id,
            metadata={
                "type": "evaluated_idea",
                "topic": topic,
                "status": status.lower(),
                "eliminated": eliminated,
                "score": score,
                "threshold": threshold,
                "timestamp": datetime.now().isoformat(),
            }
        )
        return result.get("id", "unknown")

    def save_eliminated_idea(
        self,
        topic: str,
        reason: str,
        scores: dict,
        research_insights: str = "",
        competitor_analysis: str = "",
        market_sizing: str = "",
    ) -> str:
        """Save an eliminated idea to memory (backward compatibility).

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
        score = scores.get("total", 0.0) if isinstance(scores, dict) else 0.0
        return self.save_idea(
            topic=topic,
            eliminated=True,
            score=score,
            threshold=5.0,
            reason=reason,
            research_insights=research_insights,
            competitor_analysis=competitor_analysis,
            market_sizing=market_sizing,
        )

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

    def save_phase_output(
        self,
        topic: str,
        phase: str,
        output: str,
        metadata: Optional[dict] = None,
    ) -> str:
        """Save a phase output to memory for knowledge building.

        Args:
            topic: The startup idea being evaluated
            phase: Phase name (research, competitor_analysis, market_sizing, etc.)
            output: The phase output content
            metadata: Additional metadata to store

        Returns:
            Memory ID
        """
        memory_text = f"""
Phase: {phase}
Topic: {topic}
Date: {datetime.now().isoformat()}

Output:
{output[:2000]}
"""
        meta = {
            "type": "phase_output",
            "phase": phase,
            "topic": topic,
            "timestamp": datetime.now().isoformat(),
        }
        if metadata:
            meta.update(metadata)
        
        result = self.memory.add(
            memory_text,
            user_id=self.user_id,
            metadata=meta
        )
        return result.get("id", "unknown")

    def get_market_insights(self, query: str, limit: int = 5) -> list[dict]:
        """Get market insights from past evaluations.

        Args:
            query: Search query (e.g., market trend, competitor type)
            limit: Maximum number of results

        Returns:
            List of relevant market insights
        """
        results = self.memory.search(query, user_id=self.user_id, limit=limit)
        # Filter for phase outputs and ideas
        insights = []
        for result in results.get("results", []):
            meta = result.get("metadata", {})
            if meta.get("type") in ["phase_output", "evaluated_idea"]:
                insights.append(result)
        return insights

    def get_similar_ideas_context(self, topic: str, limit: int = 3) -> str:
        """Get context about similar ideas for agent prompts.

        Args:
            topic: The new idea to find similar ones for
            limit: Maximum number of similar ideas to retrieve

        Returns:
            Formatted context string for agents
        """
        similar = self.search_similar_ideas(topic, limit=limit)
        if not similar:
            return ""
        
        context_parts = ["## Similar Ideas Evaluated Previously:\n"]
        for i, idea in enumerate(similar, 1):
            meta = idea.get("metadata", {})
            idea_topic = meta.get("topic", "Unknown")
            status = meta.get("status", "unknown")
            score = meta.get("score", 0.0)
            context_parts.append(
                f"{i}. **{idea_topic}** ({status.upper()}, Score: {score}/10)"
            )
        
        return "\n".join(context_parts)

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
            meta = top_result.get("metadata", {})
            if meta.get("eliminated", False):
                return top_result
        return None

    def get_all_ideas(self, status: Optional[str] = None, limit: int = 50) -> list[dict]:
        """Retrieve all evaluated ideas, optionally filtered by status.

        Args:
            status: Filter by status ("passed", "eliminated", or None for all)
            limit: Maximum number of ideas to retrieve

        Returns:
            List of idea memories
        """
        memories = self.memory.get_all(user_id=self.user_id)
        ideas = [m for m in memories.get("results", [])]
        
        if status:
            ideas = [
                m for m in ideas
                if m.get("metadata", {}).get("status") == status.lower()
            ]
        
        return ideas[:limit]


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
