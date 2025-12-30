"""
Mem0 Helper Scripts for Ideation Agents
Streamlined operations for reading/writing session context
"""

import os
import re
import time
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from mem0 import MemoryClient

MEM0_API_KEY = os.environ.get("MEM0_API_KEY")


def get_client(api_key: str = None) -> MemoryClient:
    """Get Mem0 client instance."""
    key = api_key or MEM0_API_KEY
    return MemoryClient(api_key=key)


def get_user_id(agent_name: str, session_id: str) -> str:
    """
    Generate consistent user_id for an agent.

    Args:
        agent_name: Name of the agent (e.g., 'market_researcher')
        session_id: Session identifier

    Returns:
        Formatted user_id string
    """
    return f"ideation_{agent_name}_{session_id}"


def initialize_session(session_id: str, problem: str, threshold: float = 5.0, api_key: str = None) -> bool:
    """
    Initialize a new evaluation session.

    Args:
        session_id: Unique session identifier
        problem: Problem statement to evaluate
        threshold: Score threshold for passing (default 5.0)
        api_key: Optional Mem0 API key

    Returns:
        True if initialization successful
    """
    client = get_client(api_key)
    user_id = get_user_id("orchestrator", session_id)

    client.add(
        f"Session initialized for problem: {problem}",
        user_id=user_id,
        metadata={
            "type": "session_init",
            "session_id": session_id,
            "problem": problem,
            "threshold": threshold,
            "status": "started"
        }
    )

    return True


def write_phase_output(
    session_id: str,
    agent_name: str,
    phase: str,
    data: Dict[str, Any],
    api_key: str = None
) -> bool:
    """
    Write phase output to Mem0.

    Args:
        session_id: Session identifier
        agent_name: Name of the agent writing
        phase: Phase name (e.g., 'market_research', 'scoring')
        data: Output data to store
        api_key: Optional Mem0 API key

    Returns:
        True if write successful
    """
    client = get_client(api_key)
    user_id = get_user_id(agent_name, session_id)

    # Write each data item as a separate memory for better retrieval
    for key, value in data.items():
        memory_text = f"{phase} {key}: {value}"
        client.add(
            memory_text,
            user_id=user_id,
            metadata={
                "type": f"{phase}_output",
                "key": key,
                "session_id": session_id,
                "agent": agent_name
            }
        )

    # Mark phase as complete
    client.add(
        f"Session {session_id} {agent_name} phase complete",
        user_id=user_id,
        metadata={
            "type": "phase_complete",
            "phase": phase,
            "session_id": session_id,
            "agent": agent_name
        }
    )

    return True


def get_session_context(session_id: str, agent_name: str = None, api_key: str = None) -> List[Dict]:
    """
    Get all context for a session from all agents.

    Args:
        session_id: Session identifier
        agent_name: Specific agent to query (optional, queries all if None)
        api_key: Optional Mem0 API key

    Returns:
        List of memory results
    """
    client = get_client(api_key)

    if agent_name:
        user_id = get_user_id(agent_name, session_id)
    else:
        user_id = get_user_id("orchestrator", session_id)

    # Use search with filters (required by Mem0 v2 API)
    results = client.search(
        f"session {session_id}",
        filters={"user_id": user_id},
        limit=100
    )

    return results.get("results", []) if isinstance(results, dict) else results


def get_agent_output(session_id: str, agent_name: str, api_key: str = None) -> List[Dict]:
    """
    Get specific agent's output for a session.

    Args:
        session_id: Session identifier
        agent_name: Name of the agent to query
        api_key: Optional Mem0 API key

    Returns:
        List of agent's memory outputs
    """
    client = get_client(api_key)
    user_id = get_user_id(agent_name, session_id)

    # Use search with filters (required by Mem0 v2 API)
    results = client.search(
        f"session {session_id}",
        filters={"user_id": user_id},
        limit=100
    )
    return results.get("results", []) if isinstance(results, dict) else results


def check_phase_complete(session_id: str, agent_name: str, api_key: str = None) -> bool:
    """
    Check if an agent has completed its phase.

    Args:
        session_id: Session identifier
        agent_name: Name of the agent to check
        api_key: Optional Mem0 API key

    Returns:
        True if phase is complete
    """
    client = get_client(api_key)
    user_id = get_user_id(agent_name, session_id)

    # Use search with filters (required by Mem0 v2 API)
    results = client.search(
        "phase complete",
        filters={"user_id": user_id},
        limit=1
    )

    if isinstance(results, dict):
        results = results.get("results", [])

    return len(results) > 0 and "complete" in results[0].get("memory", "").lower()


def wait_for_phase(
    session_id: str,
    agent_name: str,
    timeout: int = 300,
    poll_interval: int = 10,
    api_key: str = None
) -> Tuple[bool, str]:
    """
    Wait for an agent to complete its phase.

    Args:
        session_id: Session identifier
        agent_name: Name of the agent to wait for
        timeout: Maximum seconds to wait (default 300)
        poll_interval: Seconds between checks (default 10)
        api_key: Optional Mem0 API key

    Returns:
        True if phase completed, False if timeout
    """
    start_time = time.time()

    while time.time() - start_time < timeout:
        if check_phase_complete(session_id, agent_name, api_key):
            return True, ""
        time.sleep(poll_interval)

    return False, f"Timeout waiting for {agent_name} after {timeout}s"


def wait_for_agents(
    session_id: str,
    agent_names: List[str],
    timeout: int = 300,
    poll_interval: int = 10,
    api_key: str = None
) -> Dict[str, bool]:
    """
    Wait for multiple agents to complete (for parallel execution).

    Args:
        session_id: Session identifier
        agent_names: List of agent names to wait for
        timeout: Maximum seconds to wait (default 300)
        poll_interval: Seconds between checks (default 10)
        api_key: Optional Mem0 API key

    Returns:
        Dict mapping agent names to completion status
    """
    start_time = time.time()
    completed = {name: False for name in agent_names}

    while time.time() - start_time < timeout:
        all_complete = True
        for name in agent_names:
            if not completed[name]:
                if check_phase_complete(session_id, name, api_key):
                    completed[name] = True
                else:
                    all_complete = False

        if all_complete:
            return completed

        time.sleep(poll_interval)

    return completed


def get_score(session_id: str, phase: str = "problem", api_key: str = None) -> Optional[float]:
    """
    Get the score for a specific phase.

    Args:
        session_id: Session identifier
        phase: Phase to get score for ('problem' or 'solution')
        api_key: Optional Mem0 API key

    Returns:
        Score as float, or None if not found
    """
    client = get_client(api_key)
    user_id = get_user_id("feasibility_scorer", session_id)

    # Use search with filters (required by Mem0 v2 API)
    results = client.search(
        f"{phase} score",
        filters={"user_id": user_id},
        limit=5
    )

    if isinstance(results, dict):
        results = results.get("results", [])

    for result in results:
        metadata = result.get("metadata", {})
        if metadata.get("type") == "scoring_decision":
            return metadata.get("score")

    return None


def write_score(
    session_id: str,
    phase: str,
    score: float,
    decision: str,
    details: Dict = None,
    api_key: str = None
) -> bool:
    """
    Write a scoring decision to Mem0.

    Args:
        session_id: Session identifier
        phase: Phase being scored ('problem' or 'solution')
        score: Numeric score
        decision: Decision string ('pass', 'fail', 'continue')
        details: Additional scoring details
        api_key: Optional Mem0 API key

    Returns:
        True if write successful
    """
    client = get_client(api_key)
    user_id = get_user_id("feasibility_scorer", session_id)

    metadata = {
        "type": "scoring_decision",
        "phase": phase,
        "score": score,
        "decision": decision,
        "session_id": session_id
    }

    if details:
        metadata.update(details)

    client.add(
        f"Session {session_id} {phase} phase score: {score}, decision: {decision}",
        user_id=user_id,
        metadata=metadata
    )

    return True


def validate_score(score: float, criterion: str = "") -> float:
    """
    Validate score is in 1-10 range.

    Args:
        score: Score to validate
        criterion: Name of criterion (for error messages)

    Returns:
        Validated score clamped to 1-10 range

    Raises:
        ValueError if score is not a number
    """
    if not isinstance(score, (int, float)):
        raise ValueError(f"Score for {criterion} must be a number, got {type(score)}")

    if score < 1:
        print(f"Warning: {criterion} score {score} below minimum, clamping to 1")
        return 1.0
    if score > 10:
        print(f"Warning: {criterion} score {score} above maximum, clamping to 10")
        return 10.0

    return float(score)


def get_problem_scores(session_id: str, api_key: str = None) -> Dict[str, Optional[float]]:
    """
    Extract all problem validation scores from a session.

    Args:
        session_id: Session identifier
        api_key: Optional Mem0 API key

    Returns:
        Dict with keys: problem_severity, market_size, willingness_to_pay, solution_fit
    """
    client = get_client(api_key)
    scores = {
        "problem_severity": None,
        "market_size": None,
        "willingness_to_pay": None,
        "solution_fit": None
    }

    # Search customer-solution agent for scores
    customer_user_id = get_user_id("customer_solution", session_id)
    customer_results = client.search(
        "score",
        filters={"user_id": customer_user_id},
        limit=20
    )

    if isinstance(customer_results, dict):
        customer_results = customer_results.get("results", [])

    for result in customer_results:
        memory = result.get("memory", "").lower()
        metadata = result.get("metadata", {})

        # Check for solution fit score
        if metadata.get("type") == "solution_fit_score":
            scores["solution_fit"] = metadata.get("score")
        elif "solution fit" in memory:
            # Try to extract score from memory text
            match = re.search(r"(\d+(?:\.\d+)?)/10", memory)
            if match:
                scores["solution_fit"] = float(match.group(1))

    # Search market-researcher agent for market_size
    market_user_id = get_user_id("market_researcher", session_id)
    market_results = client.search(
        "market size score",
        filters={"user_id": market_user_id},
        limit=10
    )

    if isinstance(market_results, dict):
        market_results = market_results.get("results", [])

    for result in market_results:
        memory = result.get("memory", "").lower()
        if "market size" in memory:
            match = re.search(r"(\d+(?:\.\d+)?)/10", memory)
            if match:
                scores["market_size"] = float(match.group(1))

    return scores


def get_solution_scores(session_id: str, api_key: str = None) -> Dict[str, Optional[float]]:
    """
    Extract solution validation scores from feasibility-scorer.

    Args:
        session_id: Session identifier
        api_key: Optional Mem0 API key

    Returns:
        Dict with keys: technical_viability, competitive_advantage,
                       resource_requirements, time_to_market
    """
    client = get_client(api_key)
    user_id = get_user_id("feasibility_scorer", session_id)

    results = client.search(
        "score",
        filters={"user_id": user_id},
        limit=20
    )

    if isinstance(results, dict):
        results = results.get("results", [])

    scores = {
        "technical_viability": None,
        "competitive_advantage": None,
        "resource_requirements": None,
        "time_to_market": None
    }

    for result in results:
        memory = result.get("memory", "").lower()
        metadata = result.get("metadata", {})

        # Check metadata for scoring_decision
        if metadata.get("type") == "scoring_decision":
            if metadata.get("solution_score"):
                # If we have a combined solution score, use it
                pass

        # Try to extract individual scores from memory text
        for criterion in scores.keys():
            criterion_text = criterion.replace("_", " ")
            if criterion_text in memory:
                match = re.search(r"(\d+(?:\.\d+)?)/10", memory)
                if match and scores[criterion] is None:
                    scores[criterion] = float(match.group(1))

    return scores


def cache_research(
    session_id: str,
    research_type: str,
    query: str,
    results: Dict,
    ttl_hours: int = 24,
    api_key: str = None
) -> bool:
    """
    Cache research results in Mem0 to avoid duplicate searches.

    Args:
        session_id: Session identifier
        research_type: Type of research (e.g., 'web_search', 'competitor')
        query: Search query that was executed
        results: Results to cache
        ttl_hours: Time-to-live in hours (default 24)
        api_key: Optional Mem0 API key

    Returns:
        True if cache write successful
    """
    client = get_client(api_key)
    user_id = get_user_id("cache", session_id)

    cache_key = hashlib.md5(f"{research_type}:{query}".encode()).hexdigest()

    client.add(
        f"Cached {research_type}: {query[:100]}",
        user_id=user_id,
        metadata={
            "type": "research_cache",
            "cache_key": cache_key,
            "research_type": research_type,
            "query": query,
            "results": results,
            "cached_at": datetime.now().isoformat(),
            "ttl_hours": ttl_hours
        }
    )
    return True


def _is_cache_expired(result: Dict, default_ttl_hours: int = 24) -> bool:
    """Check if a cached result has expired."""
    metadata = result.get("metadata", {})
    cached_at = metadata.get("cached_at")
    ttl_hours = metadata.get("ttl_hours", default_ttl_hours)

    if not cached_at:
        return True

    try:
        cached_time = datetime.fromisoformat(cached_at)
        age_hours = (datetime.now() - cached_time).total_seconds() / 3600
        return age_hours > ttl_hours
    except (ValueError, TypeError):
        return True


def get_cached_research(
    session_id: str,
    research_type: str,
    query: str,
    api_key: str = None
) -> Optional[Dict]:
    """
    Retrieve cached research if available and not expired.

    Args:
        session_id: Session identifier
        research_type: Type of research
        query: Search query
        api_key: Optional Mem0 API key

    Returns:
        Cached results if available and not expired, None otherwise
    """
    client = get_client(api_key)
    user_id = get_user_id("cache", session_id)

    cache_key = hashlib.md5(f"{research_type}:{query}".encode()).hexdigest()

    results = client.search(
        cache_key,
        filters={"user_id": user_id},
        limit=1
    )

    if isinstance(results, dict):
        results = results.get("results", [])

    if results and not _is_cache_expired(results[0]):
        return results[0].get("metadata", {}).get("results")
    return None


if __name__ == "__main__":
    # Test the functions
    print("Testing Mem0 helper functions...")
    print("Functions available:")
    print("- initialize_session()")
    print("- write_phase_output()")
    print("- get_session_context()")
    print("- check_phase_complete()")
    print("- wait_for_phase()")
    print("- wait_for_agents()")
    print("- get_score()")
    print("- write_score()")
    print("- validate_score()")
    print("- get_problem_scores()")
    print("- get_solution_scores()")
    print("- cache_research()")
    print("- get_cached_research()")
