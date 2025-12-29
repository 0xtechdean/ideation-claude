"""
Slack Helper Scripts for Ideation Flow
Send evaluation reports and notifications to Slack
"""

import os
import requests
from typing import Dict, Optional

SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_CHANNEL_ID = os.environ.get("SLACK_CHANNEL_ID")


def post_message(text: str, channel_id: str = None, blocks: list = None) -> Dict:
    """
    Post a message to Slack.

    Args:
        text: Message text (fallback for notifications)
        channel_id: Channel to post to (defaults to SLACK_CHANNEL_ID)
        blocks: Optional Block Kit blocks for rich formatting

    Returns:
        Slack API response
    """
    channel = channel_id or SLACK_CHANNEL_ID

    headers = {
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "channel": channel,
        "text": text,
        "unfurl_links": False
    }

    if blocks:
        payload["blocks"] = blocks

    response = requests.post(
        "https://slack.com/api/chat.postMessage",
        headers=headers,
        json=payload
    )

    return response.json()


def format_evaluation_report(
    session_id: str,
    problem: str,
    score: float,
    verdict: str,
    tam: str,
    som: str,
    primary_segment: str,
    key_gap: str,
    report_path: str,
    next_steps: list
) -> list:
    """
    Format an evaluation report as Slack Block Kit blocks.

    Returns:
        List of Block Kit blocks
    """
    # Emoji based on verdict
    status_emoji = "✅" if verdict.upper() == "PASS" else "❌"

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"{status_emoji} Startup Evaluation Complete",
                "emoji": True
            }
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Session ID:*\n`{session_id}`"},
                {"type": "mrkdwn", "text": f"*Score:*\n*{score}/10*"}
            ]
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Verdict:*\n{status_emoji} *{verdict.upper()}*"},
                {"type": "mrkdwn", "text": f"*TAM:*\n{tam}"}
            ]
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Problem Statement:*\n>{problem[:200]}{'...' if len(problem) > 200 else ''}"
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Year 1 SOM:*\n{som}"},
                {"type": "mrkdwn", "text": f"*Primary Segment:*\n{primary_segment}"}
            ]
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Key Market Gap:*\n{key_gap}"
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Recommended Next Steps:*\n" + "\n".join([f"• {step}" for step in next_steps[:4]])
            }
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"📄 Full report: `{report_path}`"
                }
            ]
        }
    ]

    return blocks


def send_evaluation_report(
    session_id: str,
    problem: str,
    score: float,
    verdict: str,
    tam: str = "N/A",
    som: str = "N/A",
    primary_segment: str = "N/A",
    key_gap: str = "N/A",
    report_path: str = "",
    next_steps: list = None,
    channel_id: str = None
) -> Dict:
    """
    Send a formatted evaluation report to Slack.

    Args:
        session_id: Evaluation session ID
        problem: Problem statement
        score: Combined score (0-10)
        verdict: "PASS" or "FAIL"
        tam: Total Addressable Market
        som: Serviceable Obtainable Market (Year 1)
        primary_segment: Primary customer segment
        key_gap: Key market gap identified
        report_path: Path to full report file
        next_steps: List of recommended next steps
        channel_id: Slack channel (defaults to env var)

    Returns:
        Slack API response
    """
    next_steps = next_steps or ["Review full report", "Begin customer discovery"]

    blocks = format_evaluation_report(
        session_id=session_id,
        problem=problem,
        score=score,
        verdict=verdict,
        tam=tam,
        som=som,
        primary_segment=primary_segment,
        key_gap=key_gap,
        report_path=report_path,
        next_steps=next_steps
    )

    # Fallback text for notifications
    fallback_text = f"Startup Evaluation Complete: {verdict.upper()} ({score}/10) - Session {session_id}"

    return post_message(fallback_text, channel_id, blocks)


def send_simple_notification(
    title: str,
    message: str,
    channel_id: str = None
) -> Dict:
    """
    Send a simple notification to Slack.

    Args:
        title: Notification title
        message: Message body
        channel_id: Slack channel (defaults to env var)

    Returns:
        Slack API response
    """
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": title,
                "emoji": True
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": message
            }
        }
    ]

    return post_message(title, channel_id, blocks)


if __name__ == "__main__":
    # Test the functions
    print("Testing Slack helper functions...")
    print("Functions available:")
    print("- post_message()")
    print("- format_evaluation_report()")
    print("- send_evaluation_report()")
    print("- send_simple_notification()")
