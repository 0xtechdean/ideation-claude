"""
Mem0 Helper Scripts for Ideation Agents
Streamlined operations for reading/writing session context
"""

import os
import time
from typing import Dict, List, Optional, Any
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
) -> bool:
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
            return True
        time.sleep(poll_interval)

    return False


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
