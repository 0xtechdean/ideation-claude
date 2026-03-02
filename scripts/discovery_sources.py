"""
Discovery Sources for Ideation Pipeline (Phase 0)
API clients for 5 data sources that mine authentic user pain signals:

1. Arctic Shift - Reddit full-text body + comment search
2. PullPush - Reddit near-real-time (Pushshift replacement)
3. HN Algolia - HackerNews comments + stories
4. Federal Register - New US regulations
5. Serper Reddit dorks - Google-indexed Reddit threads (existing)

All sources return normalized signal format for clustering and ranking.
"""

import os
import re
import time
import requests
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime, timedelta, timezone
from pathlib import Path

from web_research import load_env_var, search_reddit_struggles, SERPER_API_KEY

# --- Constants ---

DEFAULT_TIMEOUT = 30

# Subreddits by vertical for targeted discovery
DEFAULT_SUBREDDITS: Dict[str, List[str]] = {
    "broad": [
        "startups", "Entrepreneur", "SaaS", "smallbusiness",
        "technology", "programming", "webdev",
    ],
    "saas": [
        "SaaS", "startups", "Entrepreneur", "smallbusiness",
        "salesforce", "hubspot", "ProductManagement",
    ],
    "devtools": [
        "programming", "webdev", "devops", "ExperiencedDevs",
        "csharp", "golang", "rust", "node", "reactjs",
        "softwarearchitecture", "learnprogramming",
    ],
    "enterprise": [
        "sysadmin", "ITManagers", "cybersecurity", "netsec",
        "devops", "aws", "azure", "googlecloud",
    ],
    "fintech": [
        "fintech", "personalfinance", "CreditCards", "Banking",
        "investing", "FinancialPlanning", "tax",
    ],
    "healthcare": [
        "healthIT", "medicine", "nursing", "pharmacy",
        "HealthInsurance", "EMR", "telehealth",
    ],
    "ai_ml": [
        "MachineLearning", "artificial", "LocalLLaMA",
        "ChatGPT", "OpenAI", "MLOps", "datascience",
    ],
    "legal": [
        "LawFirm", "Lawyertalk", "legaladvice",
        "paralegal", "LegalTech",
    ],
    "ecommerce": [
        "ecommerce", "shopify", "FulfillmentByAmazon",
        "dropship", "Etsy", "AmazonSeller",
    ],
    "education": [
        "edtech", "Teachers", "highereducation",
        "instructionaldesign", "elearning",
    ],
}

# Pain phrases organized by signal type for discovery
DISCOVERY_PAIN_PHRASES: Dict[str, List[str]] = {
    "frustration": [
        "frustrated with", "sick of", "fed up with", "hate how",
        "worst part about", "drives me crazy", "so annoying",
        "waste of time", "pain point", "nightmare",
    ],
    "seeking_alternatives": [
        "looking for alternative", "switched from", "moving away from",
        "anyone know a better", "replacement for", "competitor to",
        "something better than", "tired of using",
    ],
    "broken_workflows": [
        "manual process", "takes too long", "should be automated",
        "still using spreadsheets", "copy paste", "no integration",
        "cobbled together", "duct tape", "workaround",
    ],
    "willingness_to_pay": [
        "would pay for", "shut up and take my money", "take my money",
        "worth paying", "happy to pay", "budget for",
        "how much would", "pricing for",
    ],
    "unmet_needs": [
        "wish there was", "someone should build", "why doesn't",
        "nobody has built", "missing feature", "doesn't exist yet",
        "if only there was", "dream tool",
    ],
}


# --- Normalized Signal Format ---

def _normalize_signal(
    raw: Dict,
    source: str,
    community: str = "",
    url: str = "",
) -> Dict:
    """
    Convert raw API response into normalized signal format.

    Args:
        raw: Raw data from source API
        source: Source identifier (arctic_shift, pullpush, hn_algolia, reddit_dork, federal_register)
        community: Subreddit name, "hackernews", or "federal_register"
        url: Direct URL to the content

    Returns:
        Normalized signal dict
    """
    title = raw.get("title", "") or ""
    body = raw.get("body", "") or raw.get("selftext", "") or raw.get("text", "") or ""
    author = raw.get("author", "") or raw.get("by", "") or ""
    score = int(raw.get("score", 0) or raw.get("points", 0) or raw.get("ups", 0) or 0)
    comments = int(raw.get("num_comments", 0) or raw.get("descendants", 0) or raw.get("comments", 0) or 0)

    # Parse date
    date_str = ""
    if raw.get("created_utc"):
        try:
            ts = float(raw["created_utc"])
            date_str = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
        except (ValueError, TypeError, OSError):
            date_str = str(raw["created_utc"])
    elif raw.get("created_at"):
        date_str = str(raw["created_at"])
    elif raw.get("publication_date"):
        date_str = str(raw["publication_date"])

    # Build unique ID
    sig_id = raw.get("id", "") or raw.get("objectID", "") or raw.get("document_number", "")
    if not sig_id:
        sig_id = f"{source}_{hash(title + body[:100])}"

    return {
        "source": source,
        "title": title[:300],
        "body": body,
        "author": author,
        "score": score,
        "comments": comments,
        "date": date_str,
        "community": community or source,
        "url": url or raw.get("url", "") or raw.get("permalink", "") or "",
        "id": str(sig_id),
        "engagement": float(score + (comments * 2)),
    }


def _deduplicate_signals(signals: List[Dict]) -> List[Dict]:
    """
    Deduplicate signals by (community, id) pair.

    Args:
        signals: List of normalized signals

    Returns:
        Deduplicated list, preserving order (first seen wins)
    """
    seen: Set[Tuple[str, str]] = set()
    deduped = []

    for sig in signals:
        key = (sig["community"], sig["id"])
        if key not in seen:
            seen.add(key)
            deduped.append(sig)

    return deduped


# --- Source 1: Arctic Shift (Reddit full-text search) ---

ARCTIC_SHIFT_BASE = "https://arctic-shift.photon-reddit.com/api"


def search_arctic_shift(
    query: str,
    subreddits: Optional[List[str]] = None,
    search_type: str = "comments",
    after: Optional[str] = None,
    limit: int = 100,
    timeout: int = DEFAULT_TIMEOUT,
) -> Dict:
    """
    Search Reddit via Arctic Shift API (full-text body + comment search).

    API docs: https://github.com/ArthurHeitmann/arctic_shift/blob/master/api/README.md
    - Posts endpoint: /api/posts/search (uses "query" param for title+selftext)
    - Comments endpoint: /api/comments/search (uses "body" param)
    - "subreddit" param takes a single value, so we query each subreddit separately

    Args:
        query: Search query string
        subreddits: List of subreddit names to filter (optional)
        search_type: "comments" or "posts"
        after: ISO date string (YYYY-MM-DD) for minimum date filter
        limit: Max results (up to 100)
        timeout: Request timeout in seconds

    Returns:
        Dict with results list and metadata
    """
    # Map to correct endpoint names
    endpoint_type = "posts" if search_type in ("submissions", "posts") else "comments"
    endpoint = f"{ARCTIC_SHIFT_BASE}/{endpoint_type}/search"

    # Use correct query param per endpoint type
    # Note: Arctic Shift comments "body" param only supports single-word search.
    # For multi-word queries on comments, use only the first word.
    if endpoint_type == "comments":
        # Extract first meaningful word (skip short words)
        words = [w.strip('"') for w in query.split() if len(w.strip('"')) >= 4 and w.upper() != "OR"]
        body_term = words[0] if words else query.split()[0].strip('"')
        params = {"body": body_term, "limit": min(limit, 100), "sort": "desc"}
    else:
        params = {"query": query, "limit": min(limit, 100), "sort": "desc"}

    if after:
        params["after"] = after

    all_normalized = []
    # Arctic Shift requires subreddit param for body/query searches
    sub_list = subreddits[:5] if subreddits else ["all"]

    for sub in sub_list:
        sub_params = dict(params)
        sub_params["subreddit"] = sub

        retries = 3
        for attempt in range(retries):
            try:
                response = requests.get(endpoint, params=sub_params, timeout=timeout)

                # Arctic Shift returns 422 or 200 with rate-limit error in body
                data = response.json()
                if data.get("error"):
                    err_msg = data["error"].lower()
                    if "timeout" in err_msg or "slow down" in err_msg:
                        if attempt < retries - 1:
                            time.sleep(5 * (attempt + 1))
                            continue
                        # Final attempt failed
                        break
                    # Other error (not rate limit)
                    break

                # If HTTP error but not rate limit
                if response.status_code >= 400:
                    response.raise_for_status()

                items = data.get("data") or []

                for item in items:
                    subreddit = item.get("subreddit", sub or "")
                    permalink = item.get("permalink", "")
                    url = f"https://reddit.com{permalink}" if permalink else ""

                    sig = _normalize_signal(item, "arctic_shift", subreddit, url)
                    all_normalized.append(sig)

                break  # Success, no retry needed

            except requests.Timeout:
                if attempt < retries - 1:
                    time.sleep(5)
                    continue
                return {"error": f"Arctic Shift timed out after {timeout}s", "results": all_normalized, "source": "arctic_shift"}
            except requests.RequestException as e:
                if not all_normalized:
                    return {"error": f"Arctic Shift request failed: {str(e)}", "results": [], "source": "arctic_shift"}
                break

        time.sleep(2)  # Arctic Shift needs longer cooldown between requests

    return {
        "results": all_normalized,
        "total": len(all_normalized),
        "source": "arctic_shift",
        "search_type": search_type,
        "query": query,
    }


# --- Source 2: PullPush (Reddit near-real-time, Pushshift replacement) ---

PULLPUSH_BASE = "https://api.pullpush.io/reddit"


def search_pullpush(
    query: str,
    subreddit: Optional[str] = None,
    search_type: str = "comment",
    after: Optional[int] = None,
    limit: int = 100,
    timeout: int = DEFAULT_TIMEOUT,
) -> Dict:
    """
    Search Reddit via PullPush API (Pushshift replacement, near-real-time).

    Args:
        query: Search query string
        subreddit: Single subreddit name to filter (optional)
        search_type: "comment" or "submission"
        after: Unix timestamp for minimum date
        limit: Max results (up to 100)
        timeout: Request timeout in seconds

    Returns:
        Dict with results list and metadata
    """
    endpoint = f"{PULLPUSH_BASE}/search/{search_type}/"

    params = {
        "q": query,
        "size": min(limit, 100),
        "sort": "score",
        "sort_type": "desc",
    }

    if subreddit:
        params["subreddit"] = subreddit

    if after:
        params["after"] = after

    try:
        response = requests.get(endpoint, params=params, timeout=timeout)
        response.raise_for_status()
        data = response.json()

        items = data.get("data", [])
        normalized = []

        for item in items:
            sub = item.get("subreddit", "")
            permalink = item.get("permalink", "")
            url = f"https://reddit.com{permalink}" if permalink else ""

            sig = _normalize_signal(item, "pullpush", sub, url)
            normalized.append(sig)

        return {
            "results": normalized,
            "total": len(normalized),
            "source": "pullpush",
            "search_type": search_type,
            "query": query,
        }

    except requests.Timeout:
        return {"error": f"PullPush timed out after {timeout}s", "results": [], "source": "pullpush"}
    except requests.RequestException as e:
        return {"error": f"PullPush request failed: {str(e)}", "results": [], "source": "pullpush"}


# --- Source 3: HN Algolia (HackerNews comments + stories) ---

HN_ALGOLIA_BASE = "https://hn.algolia.com/api/v1"


def search_hn_algolia(
    query: str,
    tags: Optional[str] = None,
    after_timestamp: Optional[int] = None,
    hits_per_page: int = 50,
    timeout: int = DEFAULT_TIMEOUT,
) -> Dict:
    """
    Search HackerNews via Algolia API (comments + stories).

    Args:
        query: Search query string
        tags: Filter tags - "story", "comment", "ask_hn", "show_hn", "poll"
              Can combine: "(story,comment)" for both
        after_timestamp: Unix timestamp for minimum date
        hits_per_page: Results per page (max 1000)
        timeout: Request timeout in seconds

    Returns:
        Dict with results list and metadata
    """
    params = {
        "query": query,
        "hitsPerPage": min(hits_per_page, 1000),
    }

    if tags:
        params["tags"] = tags

    if after_timestamp:
        params["numericFilters"] = f"created_at_i>{after_timestamp}"

    try:
        response = requests.get(
            f"{HN_ALGOLIA_BASE}/search_by_date",
            params=params,
            timeout=timeout,
        )
        response.raise_for_status()
        data = response.json()

        hits = data.get("hits", [])
        normalized = []

        for hit in hits:
            hn_id = hit.get("objectID", "")
            story_id = hit.get("story_id") or hn_id
            url = f"https://news.ycombinator.com/item?id={story_id}"

            raw = {
                "title": hit.get("story_title", "") or hit.get("title", ""),
                "body": hit.get("comment_text", "") or hit.get("story_text", "") or "",
                "author": hit.get("author", ""),
                "score": hit.get("points") or 0,
                "num_comments": hit.get("num_comments") or 0,
                "created_utc": hit.get("created_at_i"),
                "id": hn_id,
                "url": hit.get("url", "") or url,
            }

            sig = _normalize_signal(raw, "hn_algolia", "hackernews", url)
            # Strip HTML from body
            sig["body"] = re.sub(r"<[^>]+>", " ", sig["body"]).strip()
            normalized.append(sig)

        return {
            "results": normalized,
            "total": data.get("nbHits", len(normalized)),
            "source": "hn_algolia",
            "query": query,
        }

    except requests.Timeout:
        return {"error": f"HN Algolia timed out after {timeout}s", "results": [], "source": "hn_algolia"}
    except requests.RequestException as e:
        return {"error": f"HN Algolia request failed: {str(e)}", "results": [], "source": "hn_algolia"}


def get_hn_who_is_hiring(months_back: int = 3, timeout: int = DEFAULT_TIMEOUT) -> Dict:
    """
    Fetch recent 'Who is Hiring?' threads from HN to find what companies are building.

    Args:
        months_back: How many months back to search (default 3)
        timeout: Request timeout in seconds

    Returns:
        Dict with hiring thread results
    """
    after_ts = int((datetime.now(tz=timezone.utc) - timedelta(days=months_back * 30)).timestamp())

    return search_hn_algolia(
        query="Ask HN: Who is hiring?",
        tags="story",
        after_timestamp=after_ts,
        hits_per_page=10,
        timeout=timeout,
    )


# --- Source 4: Federal Register API (US regulations) ---

FEDERAL_REGISTER_BASE = "https://www.federalregister.gov/api/v1"


def search_federal_register(
    doc_type: Optional[str] = "RULE",
    agencies: Optional[List[str]] = None,
    after_date: Optional[str] = None,
    keywords: Optional[str] = None,
    per_page: int = 20,
    timeout: int = DEFAULT_TIMEOUT,
) -> Dict:
    """
    Search the Federal Register for new US regulations.

    Args:
        doc_type: Document type - "RULE", "PRORULE" (proposed rule), "NOTICE", "PRESDOCU"
        agencies: List of agency slugs (e.g., ["securities-and-exchange-commission"])
        after_date: ISO date string (YYYY-MM-DD) for minimum publication date
        keywords: Search keywords
        per_page: Results per page (max 1000)
        timeout: Request timeout in seconds

    Returns:
        Dict with regulation results
    """
    params = {
        "per_page": min(per_page, 1000),
        "order": "newest",
    }

    conditions = {}

    if doc_type:
        conditions["type[]"] = doc_type

    if agencies:
        conditions["agencies[]"] = agencies

    if after_date:
        conditions["publication_date[gte]"] = after_date

    if keywords:
        conditions["term"] = keywords

    params.update({f"conditions[{k}]" if not k.startswith("conditions") else k: v
                   for k, v in conditions.items()})

    try:
        response = requests.get(
            f"{FEDERAL_REGISTER_BASE}/documents.json",
            params=params,
            timeout=timeout,
        )
        response.raise_for_status()
        data = response.json()

        results = data.get("results", [])
        normalized = []

        for doc in results:
            raw = {
                "title": doc.get("title", ""),
                "body": doc.get("abstract", "") or doc.get("excerpt", "") or "",
                "author": ", ".join(a.get("name", "") for a in doc.get("agencies", [])),
                "score": 0,
                "num_comments": doc.get("comments_count", 0) or 0,
                "publication_date": doc.get("publication_date", ""),
                "id": doc.get("document_number", ""),
                "url": doc.get("html_url", ""),
            }

            sig = _normalize_signal(raw, "federal_register", "federal_register", raw["url"])
            sig["date"] = doc.get("publication_date", "")
            # Regulations get engagement boost based on page count and comment volume
            page_count = doc.get("page_length", 0) or 0
            sig["engagement"] = float(page_count + (sig["comments"] * 5))
            normalized.append(sig)

        return {
            "results": normalized,
            "total": data.get("count", len(normalized)),
            "source": "federal_register",
        }

    except requests.Timeout:
        return {"error": f"Federal Register timed out after {timeout}s", "results": [], "source": "federal_register"}
    except requests.RequestException as e:
        return {"error": f"Federal Register request failed: {str(e)}", "results": [], "source": "federal_register"}


# --- Source 5: Serper Reddit Dorks (existing, via web_research.py) ---

def search_reddit_dorks(
    keywords: List[str],
    pain_phrases: Optional[List[str]] = None,
    num_results: int = 10,
) -> Dict:
    """
    Search Reddit via Serper Google dorks (wraps existing web_research function).

    Args:
        keywords: Topic keywords for the dork query
        pain_phrases: Custom pain phrases (uses broad default if None)
        num_results: Number of results

    Returns:
        Dict with normalized signal results
    """
    if not SERPER_API_KEY:
        return {"error": "SERPER_API_KEY not configured", "results": [], "source": "reddit_dork"}

    result = search_reddit_struggles(keywords, num_results)
    threads = result.get("threads", [])

    normalized = []
    for thread in threads:
        sig = {
            "source": "reddit_dork",
            "title": thread.get("title", ""),
            "body": thread.get("snippet", ""),
            "author": "",
            "score": 0,
            "comments": 0,
            "date": thread.get("date", ""),
            "community": _extract_subreddit(thread.get("link", "")),
            "url": thread.get("link", ""),
            "id": thread.get("link", ""),
            "engagement": 0.0,
        }
        normalized.append(sig)

    return {
        "results": normalized,
        "total": len(normalized),
        "source": "reddit_dork",
        "query": result.get("query_used", ""),
    }


def _extract_subreddit(url: str) -> str:
    """Extract subreddit name from a Reddit URL."""
    match = re.search(r"reddit\.com/r/([^/]+)", url)
    return match.group(1) if match else "reddit"


# --- Master Sweep Function ---

def run_discovery_sweep(
    market_vertical: str,
    pain_phrases: Optional[List[str]] = None,
    subreddits: Optional[List[str]] = None,
    days_back: int = 90,
    max_per_source: int = 50,
) -> Dict:
    """
    Orchestrate all 5 discovery sources for a market vertical.

    Runs each source, normalizes results, deduplicates, and returns
    a ranked list of pain signals sorted by engagement.

    Args:
        market_vertical: Market vertical key (e.g., "devtools", "fintech") or free-text
        pain_phrases: Custom pain phrases to search for (uses defaults if None)
        subreddits: Custom subreddit list (uses vertical defaults if None)
        days_back: How far back to search (default 90 days)
        max_per_source: Max results per source (default 50)

    Returns:
        Dict with all_signals, by_source counts, stats, and top signals
    """
    # Resolve subreddits
    subs = subreddits or DEFAULT_SUBREDDITS.get(market_vertical, DEFAULT_SUBREDDITS["broad"])

    # Resolve pain phrases — build query terms
    phrases = pain_phrases or []
    if not phrases:
        for category, category_phrases in DISCOVERY_PAIN_PHRASES.items():
            phrases.extend(category_phrases[:3])  # Top 3 from each category

    # Build search queries combining vertical + pain phrases
    queries = []
    if market_vertical in DEFAULT_SUBREDDITS:
        queries.append(market_vertical)
    # Add top pain phrases as queries
    pain_query_groups = [
        " OR ".join(f'"{p}"' for p in phrases[i:i + 3])
        for i in range(0, min(len(phrases), 9), 3)
    ]

    # Calculate date boundaries
    after_date = (datetime.now(tz=timezone.utc) - timedelta(days=days_back)).strftime("%Y-%m-%d")
    after_timestamp = int((datetime.now(tz=timezone.utc) - timedelta(days=days_back)).timestamp())

    all_signals = []
    source_stats = {}
    errors = []

    # --- Source 1: Arctic Shift ---
    print(f"[Discovery] Searching Arctic Shift ({len(subs)} subreddits)...")
    for pain_query in pain_query_groups[:3]:
        for search_type in ["comments", "posts"]:
            result = search_arctic_shift(
                query=pain_query,
                subreddits=subs[:5],
                search_type=search_type,
                after=after_date,
                limit=min(max_per_source, 100),
            )
            if result.get("error"):
                errors.append(f"arctic_shift ({search_type}): {result['error']}")
            all_signals.extend(result.get("results", []))
            time.sleep(0.5)  # Rate limiting

    source_stats["arctic_shift"] = len([s for s in all_signals if s["source"] == "arctic_shift"])

    # --- Source 2: PullPush ---
    print(f"[Discovery] Searching PullPush ({len(subs)} subreddits)...")
    for sub in subs[:5]:  # Limit to top 5 subreddits
        for search_type in ["comment", "submission"]:
            for pain_query in pain_query_groups[:2]:
                result = search_pullpush(
                    query=pain_query,
                    subreddit=sub,
                    search_type=search_type,
                    after=after_timestamp,
                    limit=min(max_per_source // 5, 25),
                )
                if result.get("error"):
                    errors.append(f"pullpush ({sub}/{search_type}): {result['error']}")
                all_signals.extend(result.get("results", []))
                time.sleep(0.3)

    source_stats["pullpush"] = len([s for s in all_signals if s["source"] == "pullpush"])

    # --- Source 3: HN Algolia ---
    print("[Discovery] Searching HN Algolia...")
    for pain_query in pain_query_groups[:3]:
        for tags in ["comment", "story"]:
            result = search_hn_algolia(
                query=pain_query,
                tags=tags,
                after_timestamp=after_timestamp,
                hits_per_page=min(max_per_source, 50),
            )
            if result.get("error"):
                errors.append(f"hn_algolia ({tags}): {result['error']}")
            all_signals.extend(result.get("results", []))
            time.sleep(0.3)

    # Also check Who is Hiring threads
    wih_result = get_hn_who_is_hiring(months_back=3)
    all_signals.extend(wih_result.get("results", []))

    source_stats["hn_algolia"] = len([s for s in all_signals if s["source"] == "hn_algolia"])

    # --- Source 4: Federal Register ---
    print("[Discovery] Searching Federal Register...")
    for doc_type in ["RULE", "PRORULE"]:
        result = search_federal_register(
            doc_type=doc_type,
            after_date=after_date,
            keywords=market_vertical if market_vertical not in DEFAULT_SUBREDDITS else None,
            per_page=min(max_per_source, 20),
        )
        if result.get("error"):
            errors.append(f"federal_register ({doc_type}): {result['error']}")
        all_signals.extend(result.get("results", []))
        time.sleep(0.3)

    source_stats["federal_register"] = len([s for s in all_signals if s["source"] == "federal_register"])

    # --- Source 5: Serper Reddit Dorks ---
    print("[Discovery] Searching Reddit via Serper dorks...")
    dork_keywords = [market_vertical] if market_vertical not in DEFAULT_SUBREDDITS else [market_vertical, "software tools"]
    dork_result = search_reddit_dorks(dork_keywords, num_results=max_per_source)
    if dork_result.get("error"):
        errors.append(f"reddit_dork: {dork_result['error']}")
    all_signals.extend(dork_result.get("results", []))

    source_stats["reddit_dork"] = len([s for s in all_signals if s["source"] == "reddit_dork"])

    # --- Deduplicate ---
    before_dedup = len(all_signals)
    all_signals = _deduplicate_signals(all_signals)
    after_dedup = len(all_signals)

    # --- Truncate body for sweep results ---
    for sig in all_signals:
        if len(sig.get("body", "")) > 500:
            sig["body"] = sig["body"][:500] + "..."

    # --- Sort by engagement (desc) ---
    all_signals.sort(key=lambda s: s["engagement"], reverse=True)

    # --- Top signals ---
    top_signals = all_signals[:30]

    return {
        "all_signals": all_signals,
        "top_signals": top_signals,
        "source_stats": source_stats,
        "total_raw": before_dedup,
        "total_deduped": after_dedup,
        "duplicates_removed": before_dedup - after_dedup,
        "market_vertical": market_vertical,
        "subreddits_searched": subs,
        "days_back": days_back,
        "errors": errors,
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
    }


# --- Self-test ---

if __name__ == "__main__":
    import json

    print("=" * 60)
    print("Discovery Sources - Self Test")
    print("=" * 60)

    # Test 1: Arctic Shift
    print("\n--- 1. Arctic Shift (Reddit full-text) ---")
    as_result = search_arctic_shift("frustrated", subreddits=["programming"], limit=5)
    print(f"  Status: {'OK' if not as_result.get('error') else 'ERROR: ' + as_result['error']}")
    print(f"  Results: {as_result.get('total', 0)}")
    if as_result.get("results"):
        print(f"  Sample: {as_result['results'][0]['title'][:80]}")

    # Test 2: PullPush
    print("\n--- 2. PullPush (Reddit near-real-time) ---")
    pp_result = search_pullpush("wish there was", subreddit="SaaS", limit=5)
    print(f"  Status: {'OK' if not pp_result.get('error') else 'ERROR: ' + pp_result['error']}")
    print(f"  Results: {pp_result.get('total', 0)}")
    if pp_result.get("results"):
        print(f"  Sample: {pp_result['results'][0]['title'][:80] or pp_result['results'][0]['body'][:80]}")

    # Test 3: HN Algolia
    print("\n--- 3. HN Algolia (HackerNews) ---")
    hn_result = search_hn_algolia("frustrated with developer tools", tags="comment", hits_per_page=5)
    print(f"  Status: {'OK' if not hn_result.get('error') else 'ERROR: ' + hn_result['error']}")
    print(f"  Results: {hn_result.get('total', 0)}")
    if hn_result.get("results"):
        print(f"  Sample: {hn_result['results'][0]['body'][:80]}")

    # Test 4: Federal Register
    print("\n--- 4. Federal Register (US regulations) ---")
    after = (datetime.now(tz=timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")
    fr_result = search_federal_register(doc_type="RULE", after_date=after, per_page=5)
    print(f"  Status: {'OK' if not fr_result.get('error') else 'ERROR: ' + fr_result['error']}")
    print(f"  Results: {fr_result.get('total', 0)}")
    if fr_result.get("results"):
        print(f"  Sample: {fr_result['results'][0]['title'][:80]}")

    # Test 5: Serper Reddit Dorks
    print("\n--- 5. Serper Reddit Dorks ---")
    rd_result = search_reddit_dorks(["developer tools", "workflow"], num_results=5)
    print(f"  Status: {'OK' if not rd_result.get('error') else 'ERROR: ' + rd_result['error']}")
    print(f"  Results: {rd_result.get('total', 0)}")
    if rd_result.get("results"):
        print(f"  Sample: {rd_result['results'][0]['title'][:80]}")

    # Summary
    print("\n" + "=" * 60)
    total = sum(1 for r in [as_result, pp_result, hn_result, fr_result, rd_result] if not r.get("error"))
    print(f"Sources working: {total}/5")
    print("=" * 60)
