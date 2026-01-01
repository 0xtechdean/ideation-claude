# Coding Standards

## Python Scripts

### Style
- Use type hints for function parameters and returns
- Use docstrings for all public functions
- Follow PEP 8 naming conventions
- Keep functions focused and single-purpose

### Error Handling
```python
# Good: Handle API errors gracefully
try:
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json()
except requests.RequestException as e:
    print(f"API error: {e}")
    return {"ok": False, "error": str(e)}
```

### Environment Variables
```python
# Good: Use fallback loading
def load_credentials():
    token = os.environ.get("SLACK_BOT_TOKEN")
    if not token:
        # Try loading from .env file
        env_path = Path(__file__).parent.parent / ".env"
        # ... load from file
    return token
```

## Agent Definitions

### Structure
```markdown
---
name: agent-name
description: Clear description of agent's role
tools: Read, Grep, Glob, WebSearch, WebFetch, Bash
model: opus
---

# Agent Title

## Your Tasks
1. First task
2. Second task

## Output Format
- Always write to Mem0
- Include scores and sources
```

### Naming
- Use kebab-case for agent files: `market-researcher.md`
- Use descriptive names that indicate the agent's role

## Reports

### Structure
1. Executive Summary
2. Scores Summary Table
3. Detailed Analysis Sections
4. Sources/References

### Markdown
- Use tables for data
- Use headers for sections
- Include sources with URLs
