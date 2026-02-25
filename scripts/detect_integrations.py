"""
Detect available integrations by reading env vars with .env fallback.
Outputs JSON so the orchestrator can reliably detect MEM0, Slack, etc.

Usage:
    python scripts/detect_integrations.py
"""

import json
import os
from pathlib import Path


def load_env_var(var_name: str) -> str | None:
    """Load env var from shell environment or .env file."""
    value = os.environ.get(var_name)
    if value:
        return value

    env_paths = [
        Path(__file__).parent.parent / ".env",
        Path.cwd() / ".env",
    ]

    for env_path in env_paths:
        if env_path.exists():
            try:
                with open(env_path) as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith(f"{var_name}=") and not line.startswith("#"):
                            return line.split("=", 1)[1].strip().strip('"').strip("'")
            except Exception:
                continue

    return None


def detect() -> dict:
    mem0_key = load_env_var("MEM0_API_KEY")
    slack_token = load_env_var("SLACK_BOT_TOKEN")
    slack_channel = load_env_var("SLACK_CHANNEL_ID")
    serper_key = load_env_var("SERPER_API_KEY")

    return {
        "use_mem0": bool(mem0_key),
        "use_slack": bool(slack_token) and bool(slack_channel),
        "use_serper": bool(serper_key),
        "MEM0_API_KEY": mem0_key,
        "SLACK_BOT_TOKEN": slack_token,
        "SLACK_CHANNEL_ID": slack_channel,
        "SERPER_API_KEY": serper_key,
    }


if __name__ == "__main__":
    print(json.dumps(detect(), indent=2))
