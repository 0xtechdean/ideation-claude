"""
Slack Helper Scripts for Ideation Flow
Send evaluation reports and notifications to Slack

Key Functions:
- markdown_to_slack(): Convert GitHub markdown to Slack mrkdwn format
- send_full_report(): Send full report as properly formatted Slack messages
- send_evaluation_report(): Send summary with Block Kit formatting
"""

import os
import re
import time
import requests
from typing import Dict, List, Optional
from pathlib import Path


def load_slack_credentials() -> tuple:
    """
    Load Slack credentials from environment or .env file.

    Returns:
        Tuple of (bot_token, channel_id)
    """
    bot_token = os.environ.get("SLACK_BOT_TOKEN")
    channel_id = os.environ.get("SLACK_CHANNEL_ID")

    # If not in environment, try loading from .env file
    if not bot_token or not channel_id:
        env_paths = [
            Path(__file__).parent.parent / ".env",  # scripts/../.env
            Path.cwd() / ".env",  # current directory
        ]

        for env_path in env_paths:
            if env_path.exists():
                with open(env_path, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("SLACK_BOT_TOKEN=") and not bot_token:
                            bot_token = line.split("=", 1)[1].strip()
                        elif line.startswith("SLACK_CHANNEL_ID=") and not channel_id:
                            channel_id = line.split("=", 1)[1].strip()
                break

    return bot_token, channel_id


SLACK_BOT_TOKEN, SLACK_CHANNEL_ID = load_slack_credentials()


def format_table_for_slack(table_text: str) -> str:
    """
    Convert a markdown table to a clean Slack-friendly format.

    For competitive matrices, uses emoji checkmarks.
    For other tables, uses clean aligned rows.
    """
    lines = table_text.strip().split('\n')
    if len(lines) < 2:
        return table_text

    # Parse header and rows
    header_line = lines[0]
    # Skip separator line (lines[1])
    data_lines = lines[2:] if len(lines) > 2 else []

    # Extract cells from each line
    def parse_row(line):
        cells = [c.strip() for c in line.split('|')]
        # Remove empty first/last from | delimiters
        return [c for c in cells if c]

    headers = parse_row(header_line)
    rows = [parse_row(line) for line in data_lines]

    if not headers:
        return table_text

    # Check if this is a competitive matrix (has checkmarks/x marks)
    is_matrix = ('✅' in table_text or '❌' in table_text or
                 'Yes' in table_text or 'Partial' in table_text)

    # Only use special formatting for competitive matrices
    # Regular tables stay as code blocks
    if not is_matrix:
        return "```\n" + table_text + "```"

    result_lines = []

    # Format competitive matrix with bullet points
    for row in rows:
        if not row:
            continue

        # First column is the feature name
        key = row[0] if row else ""

        result_lines.append(f"*{key}*")
        for i, val in enumerate(row[1:], 1):
            if i < len(headers):
                comp_name = headers[i]
                # Convert Yes/No to emoji
                display_val = val.replace('Yes', '✅').replace('No', '❌')
                display_val = display_val.replace('Partial', '◐')
                result_lines.append(f"  • {comp_name}: {display_val}")
        result_lines.append("")

    return '\n'.join(result_lines)


def markdown_to_slack(text: str) -> str:
    """
    Convert GitHub-flavored Markdown to Slack mrkdwn format.

    Conversions:
    - **bold** -> *bold*
    - ## Header -> *Header*
    - [text](url) -> <url|text>
    - Tables -> clean formatted rows (not code blocks)
    - --- -> unicode line

    Args:
        text: Markdown formatted text

    Returns:
        Slack mrkdwn formatted text
    """
    # Convert headers: ## Header -> *Header*
    text = re.sub(r'^#{1,6}\s+(.+)$', r'*\1*', text, flags=re.MULTILINE)

    # Convert bold: **text** -> *text*
    text = re.sub(r'\*\*(.+?)\*\*', r'*\1*', text)

    # Convert links: [text](url) -> <url|text>
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<\2|\1>', text)

    # Convert markdown tables to clean Slack format
    def convert_table(match):
        table = match.group(0)
        return format_table_for_slack(table)

    # Find markdown tables and convert to Slack format
    table_pattern = r'(\|[^\n]+\|\n)(\|[-:| ]+\|\n)((?:\|[^\n]+\|\n?)+)'
    text = re.sub(table_pattern, convert_table, text)

    # Remove horizontal rules (---) and replace with unicode line
    text = re.sub(r'^---+$', '━' * 40, text, flags=re.MULTILINE)

    # Clean up multiple blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text


def split_message(text: str, max_len: int = 3500) -> List[str]:
    """
    Split text into chunks suitable for Slack messages.
    Tries to split at section boundaries for readability.

    Args:
        text: Text to split
        max_len: Maximum length per chunk

    Returns:
        List of text chunks
    """
    def split_long_text(text: str, max_len: int) -> List[str]:
        """Split text that exceeds max_len by lines, then by characters."""
        if len(text) <= max_len:
            return [text]

        result = []
        lines = text.split('\n')
        current = ""

        for line in lines:
            # If single line exceeds max, split by characters
            if len(line) > max_len:
                if current.strip():
                    result.append(current.strip())
                    current = ""
                # Split long line into chunks
                for i in range(0, len(line), max_len - 100):
                    result.append(line[i:i + max_len - 100])
            elif len(current) + len(line) + 1 < max_len:
                current += line + '\n'
            else:
                if current.strip():
                    result.append(current.strip())
                current = line + '\n'

        if current.strip():
            result.append(current.strip())

        return result

    # Try to split by bold headers (sections in Slack format)
    sections = re.split(r'(\n\*[^*\n]+\*\n)', text)
    chunks = []
    current = ""

    for section in sections:
        if len(current) + len(section) < max_len:
            current += section
        else:
            if current.strip():
                chunks.append(current.strip())
            # If single section is too long, split it
            if len(section) > max_len:
                # First try paragraphs
                paragraphs = section.split('\n\n')
                current = ""
                for para in paragraphs:
                    if len(para) > max_len:
                        # Paragraph too long, split by lines
                        if current.strip():
                            chunks.append(current.strip())
                            current = ""
                        chunks.extend(split_long_text(para, max_len))
                    elif len(current) + len(para) + 2 < max_len:
                        current += para + '\n\n'
                    else:
                        if current.strip():
                            chunks.append(current.strip())
                        current = para + '\n\n'
            else:
                current = section

    if current.strip():
        chunks.append(current.strip())

    return chunks


def send_full_report(
    report_path: str,
    channel_id: str = None,
    session_id: str = "",
    verdict: str = "",
    score: float = 0
) -> Dict:
    """
    Send a full report to Slack, properly formatted for Slack mrkdwn.

    The report is:
    1. Converted from Markdown to Slack mrkdwn format
    2. Split into chunks that fit Slack's message limits
    3. Sent as multiple messages with rate limiting

    Args:
        report_path: Path to the markdown report file
        channel_id: Slack channel (defaults to SLACK_CHANNEL_ID)
        session_id: Session ID for header message
        verdict: PASS/FAIL for header
        score: Combined score for header

    Returns:
        Dict with status and message count
    """
    channel = channel_id or SLACK_CHANNEL_ID

    # Read the report
    with open(report_path, "r") as f:
        content = f.read()

    # Convert to Slack format
    slack_content = markdown_to_slack(content)

    # Split into chunks
    chunks = split_message(slack_content)

    # Send header message first
    status_emoji = "✅" if verdict.upper() == "PASS" else "❌"
    header = f"{status_emoji} *Full Evaluation Report* - Session `{session_id}` - Score: *{score}/10* - Verdict: *{verdict}*"

    results = []

    # Send header
    response = post_message(header, channel)
    results.append(response)
    time.sleep(0.3)

    # Send each chunk
    for i, chunk in enumerate(chunks):
        response = post_message(chunk, channel)
        results.append(response)
        time.sleep(0.3)  # Rate limiting

    # Check results
    success_count = sum(1 for r in results if r.get("ok"))

    return {
        "ok": success_count == len(results),
        "messages_sent": success_count,
        "total_chunks": len(chunks) + 1,  # +1 for header
        "errors": [r.get("error") for r in results if not r.get("ok")]
    }


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


def send_moat_assessment(
    session_id: str,
    true_moats: List[Dict[str, str]],
    not_moats: List[Dict[str, str]],
    unique_differentiator: str,
    competitors_analyzed: str,
    verdict: str,
    channel_id: str = None
) -> Dict:
    """
    Send a moat assessment to Slack with proper formatting.

    Args:
        session_id: Evaluation session ID
        true_moats: List of dicts with 'name', 'description', 'replication_time'
        not_moats: List of dicts with 'name', 'reason'
        unique_differentiator: The ONE unique differentiator
        competitors_analyzed: String listing competitors
        verdict: GO / PIVOT / STOP
        channel_id: Slack channel (defaults to env var)

    Returns:
        Slack API response

    Example:
        send_moat_assessment(
            session_id="abc123",
            true_moats=[
                {"name": "Work Context ML", "description": "Detects if WORK is authorized", "replication_time": "18-24 mo"},
                {"name": "Data Network Effects", "description": "Shared threat intel", "replication_time": "12-18 mo"},
            ],
            not_moats=[
                {"name": "Low pricing", "reason": "Competitors match overnight"},
                {"name": "MCP support", "reason": "5+ gateways exist"},
            ],
            unique_differentiator="Work Context ML - Detecting if the WORK being done is authorized for the DATA",
            competitors_analyzed="Airia ($100M), Reco ($65M), Lasso ($28M)",
            verdict="GO - with pivot"
        )
    """
    # Format true moats
    moats_text = "\n".join([
        f"• *{m['name']}* - {m['description']}. _{m['replication_time']} to replicate._"
        for m in true_moats
    ])

    # Format not moats
    not_moats_text = "\n".join([
        f"• {m['name']} - {m['reason']}"
        for m in not_moats
    ])

    # Determine emoji based on verdict
    if "GO" in verdict.upper():
        verdict_emoji = "✅"
    elif "PIVOT" in verdict.upper():
        verdict_emoji = "🔄"
    else:
        verdict_emoji = "🛑"

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"🏰 Moat Assessment - Session {session_id}",
                "emoji": True
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Competitive Edge Analysis Complete*\nHere's what IS and ISN'T defensible."
            }
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*✅ TRUE MOATS (Defensible)*"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": moats_text
            }
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*❌ NOT MOATS (Easily Replicated)*"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": not_moats_text
            }
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*🎯 The ONE Unique Differentiator*\n\n{unique_differentiator}"
            }
        },
        {"type": "divider"},
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Competitors Analyzed:*\n{competitors_analyzed}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Verdict:*\n{verdict_emoji} *{verdict}*"
                }
            ]
        }
    ]

    fallback_text = f"Moat Assessment - Session {session_id} - Verdict: {verdict}"

    return post_message(fallback_text, channel_id, blocks)


if __name__ == "__main__":
    # Test the functions
    print("Slack Helper Functions for Ideation Flow")
    print("=" * 50)
    print("\nCredentials loaded:", "✅" if SLACK_BOT_TOKEN else "❌")
    print(f"Channel ID: {SLACK_CHANNEL_ID or 'Not set'}")
    print("\nAvailable functions:")
    print("  - markdown_to_slack(text)        # Convert markdown to Slack mrkdwn")
    print("  - split_message(text)            # Split long text into chunks")
    print("  - send_full_report(report_path)  # Send full report to Slack")
    print("  - post_message(text)             # Send simple message")
    print("  - send_evaluation_report(...)    # Send formatted summary")
    print("  - send_simple_notification(...)  # Send simple notification")
    print("\nExample usage:")
    print('  from scripts.slack_helpers import send_full_report')
    print('  send_full_report("reports/my-report.md", session_id="abc123", verdict="PASS", score=8.5)')
