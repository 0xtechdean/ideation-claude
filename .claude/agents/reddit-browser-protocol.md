---
name: reddit-browser-protocol
description: Reusable Playwright MCP instructions for browsing Reddit. Not a standalone agent — referenced by market-researcher, customer-solution, and report-pivot agents.
---

# Reddit Browser Protocol (Playwright MCP)

This document describes how to browse Reddit using Playwright MCP tools to extract real user posts, comments, and quotes. Use `old.reddit.com` for all browsing — it's server-rendered HTML that works reliably with `browser_snapshot`.

## Why old.reddit.com

- **Server-rendered HTML** — full content loads on first page load, no JS hydration needed
- **Simple DOM** — clean text content visible in `browser_snapshot` output
- **Less aggressive bot detection** — fewer CAPTCHAs and blocks than new Reddit
- **Full content on page** — comments, scores, and usernames all present in initial HTML

## Step-by-Step: Search Reddit

### 1. Generate Search URLs

```python
import sys, os
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(repo_root, 'scripts'))
from web_research import build_reddit_search_urls, suggest_subreddits

# Get relevant subreddits for the industry
subreddits = suggest_subreddits("legal", ["legal research", "small law firms"])
# Returns: ["law", "LawFirm", "legaltech", "Lawyertalk", ...]

# Generate search URLs for each pain category
urls = build_reddit_search_urls(
    keywords=["legal research", "small law firms"],
    subreddits=subreddits[:3],  # Top 3 most relevant
    categories=["usability", "cost", "gaps"],  # Focus on key categories
    time_filter="year"
)
# Returns list of dicts: {url, category, query, subreddit}
```

### 2. Browse Search Results

For each search URL:

```
1. Use `browser_navigate` to go to the URL
2. Use `browser_snapshot` to read the search results page
3. From the snapshot, identify 2-3 promising thread titles and their URLs
4. Thread URLs will be in format: /r/{sub}/comments/{id}/{slug}/
```

### 3. Read a Thread

For each promising thread:

```
1. Navigate to the thread URL on old.reddit.com
   - If URL is reddit.com/r/..., change to old.reddit.com/r/...
2. Use `browser_snapshot` to read the thread
3. Extract from the snapshot:
   - **Post title** and **post body** (the OP's text)
   - **Post author**: u/username
   - **Post score**: upvote count
   - **Subreddit**: r/subreddit_name
   - **Top 10-15 comments** with:
     - Comment text (verbatim)
     - Comment author: u/username
     - Comment score: upvote count
4. If the thread is long, use `browser_scroll_down` then `browser_snapshot` again
   to get more comments
```

### 4. Subreddit-Specific Search

For targeted searches within a specific subreddit:

```
URL format: https://old.reddit.com/r/{subreddit}/search?q={query}&restrict_sr=on&sort=relevance&t=year

The `restrict_sr=on` parameter limits search to that subreddit only.
```

## Output Format

For each thread browsed, record:

```markdown
### Thread: [Thread Title]
- **URL**: https://old.reddit.com/r/{sub}/comments/{id}/{slug}/
- **Subreddit**: r/{sub}
- **Author**: u/{username}
- **Score**: {upvotes} upvotes
- **Pain Category**: {category}

**Post Body:**
> [Verbatim text of the original post, or key excerpt]

**Top Comments:**

1. > "[Verbatim comment text]"
   > — u/{username}, {score} upvotes

2. > "[Verbatim comment text]"
   > — u/{username}, {score} upvotes

3. > "[Verbatim comment text]"
   > — u/{username}, {score} upvotes
```

## Fallback Chain

If Playwright tools are unavailable or fail:

1. **Tier 1 (Primary)**: Playwright MCP → `browser_navigate` + `browser_snapshot` on `old.reddit.com`
2. **Tier 2 (Fallback)**: `WebFetch` on `old.reddit.com` URLs (may work for some pages)
3. **Tier 3 (Last resort)**: Serper dork search via `search_reddit_struggles()` from `web_research.py` (returns Google results about Reddit, not actual Reddit content)

Always try Tier 1 first. Only fall back if you get errors from Playwright tools.

## Rate Limiting

- **Wait 2-3 seconds** between page navigations (Reddit may rate-limit rapid requests)
- **Max 3-5 threads per pain category** (diminishing returns beyond this)
- **Max 15-20 total threads** per research session
- If you hit a rate limit page or CAPTCHA, wait 10 seconds and try a different subreddit

## What Makes Good Reddit Data

**High-value signals:**
- Posts with 10+ upvotes (community validates the pain)
- Comments describing workarounds or DIY solutions (proves willingness to pay)
- "I wish..." or "someone should build..." comments (direct demand signal)
- Specific dollar amounts or time costs mentioned (quantified pain)
- Multiple users confirming the same frustration (frequency signal)

**Low-value signals (skip these):**
- Posts with 0-1 upvotes and no comments (unvalidated)
- Promotional posts or "check out my tool" threads
- Very old posts (>2 years) with no recent activity
- Meta/joke threads

## Quality Gate

After browsing Reddit, verify your output includes:
- [ ] At least 3 real thread URLs from old.reddit.com
- [ ] At least 3 verbatim user quotes with `u/` attribution
- [ ] Upvote counts for threads and key comments
- [ ] Subreddit names where the problem is discussed
- [ ] Pain category classification for each thread

If any of these are missing, your Reddit research is INCOMPLETE.
