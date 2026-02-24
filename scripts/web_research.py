"""
Web Research Helper Scripts for Ideation Agents
Uses Serper API for web searches, Google Trends, and X (Twitter) data
"""

import os
import requests
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from pathlib import Path


def load_env_var(var_name: str) -> Optional[str]:
    """
    Load environment variable from env or .env file.

    Args:
        var_name: Name of the environment variable

    Returns:
        Value if found, None otherwise
    """
    # First try environment
    value = os.environ.get(var_name)
    if value:
        return value

    # Try loading from .env file
    env_paths = [
        Path(__file__).parent.parent / ".env",  # scripts/../.env
        Path.cwd() / ".env",  # current directory
    ]

    for env_path in env_paths:
        if env_path.exists():
            try:
                with open(env_path, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith(f"{var_name}="):
                            return line.split("=", 1)[1].strip().strip('"').strip("'")
            except Exception:
                continue

    return None


SERPER_API_KEY = load_env_var("SERPER_API_KEY")
SERPER_BASE_URL = "https://google.serper.dev"

# Optional: X (Twitter) API credentials
X_BEARER_TOKEN = load_env_var("X_BEARER_TOKEN")

# Default timeout for HTTP requests (seconds)
DEFAULT_TIMEOUT = 30


def search_web(query: str, num_results: int = 10, timeout: int = DEFAULT_TIMEOUT) -> Dict:
    """
    Perform a web search using Serper API with timeout and error handling.

    Args:
        query: Search query string
        num_results: Number of results to return (default 10)
        timeout: Request timeout in seconds (default 30)

    Returns:
        Dict with search results including organic results, knowledge graph, etc.
        On error, returns dict with "error" key and empty "organic" list.
    """
    if not SERPER_API_KEY:
        return {"error": "SERPER_API_KEY not configured", "organic": []}

    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "q": query,
        "num": num_results
    }

    try:
        response = requests.post(
            f"{SERPER_BASE_URL}/search",
            headers=headers,
            json=payload,
            timeout=timeout
        )
        response.raise_for_status()
        return response.json()
    except requests.Timeout:
        return {"error": f"Search timed out after {timeout}s", "organic": []}
    except requests.HTTPError as e:
        return {"error": f"HTTP error: {e.response.status_code}", "organic": []}
    except requests.RequestException as e:
        return {"error": f"Request failed: {str(e)}", "organic": []}


def search_market_data(industry: str, keywords: List[str] = None) -> Dict:
    """
    Search for market data, trends, and statistics for an industry.

    Args:
        industry: Industry or market to research
        keywords: Additional keywords to include in search

    Returns:
        Dict with market size, growth rates, and trend data
    """
    queries = [
        f"{industry} market size 2024 2025",
        f"{industry} industry growth rate forecast",
        f"{industry} market trends statistics",
    ]

    if keywords:
        queries.extend([f"{industry} {kw}" for kw in keywords])

    results = {
        "market_size": search_web(queries[0], 5),
        "growth_forecast": search_web(queries[1], 5),
        "trends": search_web(queries[2], 5)
    }

    return results


def search_competitors(industry: str, product_type: str = None) -> List[Dict]:
    """
    Search for competitors in a specific industry.

    Args:
        industry: Industry to search competitors in
        product_type: Specific product type (optional)

    Returns:
        List of competitor information
    """
    query = f"{industry} competitors companies"
    if product_type:
        query = f"{product_type} {industry} competitors alternatives"

    results = search_web(query, 15)

    # Also search for comparison articles
    comparison_query = f"{industry} tools comparison review 2024"
    comparison_results = search_web(comparison_query, 10)

    return {
        "competitors": results.get("organic", []),
        "comparisons": comparison_results.get("organic", []),
        "knowledge_graph": results.get("knowledgeGraph", {})
    }


def search_pricing_data(product_type: str, industry: str = None) -> Dict:
    """
    Search for pricing information and models.

    Args:
        product_type: Type of product/service
        industry: Industry context (optional)

    Returns:
        Dict with pricing data and models
    """
    query = f"{product_type} pricing plans cost"
    if industry:
        query = f"{industry} {product_type} pricing"

    results = search_web(query, 10)

    return {
        "pricing_info": results.get("organic", []),
        "answer_box": results.get("answerBox", {})
    }


# Pain keyword categories for Reddit mining.
# Each category targets a different type of frustration.
PAIN_CATEGORIES: Dict[str, List[str]] = {
    "usability": [
        "confusing", "not user friendly", "bad UI", "too complicated",
        "overwhelming", "hard to use", "unintuitive",
    ],
    "failure": [
        "doesn't work", "broken", "lost money", "mistake",
        "frustration", "not working", "failed", "gave up",
    ],
    "trust": [
        "scam", "hacked", "risky", "no transparency",
        "sketchy", "shady", "don't trust",
    ],
    "cost": [
        "too expensive", "fees too high", "not worth it",
        "overpriced", "waste of money", "can't afford",
    ],
    "gaps": [
        "no good tool", "where do I start", "what I wish I knew",
        "nobody built", "wish there was", "why isn't there",
        "someone should build",
    ],
}

FIRST_PERSON_FILTERS: List[str] = [
    "I think", "my experience", "I realized", "I learned",
    "my biggest struggle", "I found that", "IMO",
    "I've been", "I was", "my biggest fear",
]


def _build_reddit_dork(
    keywords: List[str],
    pain_category: Optional[str] = None,
) -> str:
    """
    Build a Google search dork that surfaces authentic first-person
    struggles and pain points from Reddit comment threads.

    Uses the Reddit Pain-Point Mining technique: topic keywords +
    first-person language filters + categorized pain keywords.

    Args:
        keywords: Topic keywords (e.g., ["legal research", "small law firms"])
        pain_category: Optional specific category to target. One of:
            "usability", "failure", "trust", "cost", "gaps".
            If None, uses a broad mix across all categories.

    Returns:
        Google dork query string targeting Reddit pain discussions
    """
    topic = " OR ".join(f'"{kw}"' for kw in keywords)

    first_person = " OR ".join(f'"{fp}"' for fp in FIRST_PERSON_FILTERS)

    if pain_category and pain_category in PAIN_CATEGORIES:
        pain_words = PAIN_CATEGORIES[pain_category]
    else:
        # Broad mix: pick representative words from each category
        pain_words = [
            "confusing", "too complicated",          # usability
            "doesn't work", "frustration",            # failure
            "scam", "risky",                          # trust
            "too expensive", "not worth it",          # cost
            "no good tool", "what I wish I knew",     # gaps
        ]

    pain = " OR ".join(f'"{pw}"' for pw in pain_words)

    return f"{topic} site:reddit.com inurl:comments ({first_person}) ({pain})"


def search_reddit_struggles(
    keywords: List[str],
    num_results: int = 10,
    pain_category: Optional[str] = None,
) -> Dict:
    """
    Search Reddit for authentic first-person pain points using targeted
    Google dork that filters for real user experiences in comment threads.

    Args:
        keywords: Topic keywords to search for (1-3 phrases work best)
        num_results: Number of results to return
        pain_category: Optional pain category to focus on. One of:
            "usability", "failure", "trust", "cost", "gaps".
            If None, uses a broad mix.

    Returns:
        Dict with Reddit pain point threads and the query used
    """
    query = _build_reddit_dork(keywords, pain_category)
    results = search_web(query, num_results)

    return {
        "threads": results.get("organic", []),
        "query_used": query,
        "pain_category": pain_category or "broad",
        "source": "reddit_dork",
    }


def mine_reddit_pain_points(
    keywords: List[str],
    categories: Optional[List[str]] = None,
    results_per_category: int = 5,
) -> Dict:
    """
    Full Reddit pain-point mining: run multiple targeted queries across
    pain categories, then return structured results for analysis.

    This implements the multi-query approach: for each pain category,
    a separate dork is built so results target different sub-problems.

    Args:
        keywords: Topic keywords (e.g., ["crypto wallet", "seed phrase"])
        categories: Pain categories to mine. Defaults to all five:
            ["usability", "failure", "trust", "cost", "gaps"].
        results_per_category: Results per category query (default 5)

    Returns:
        Dict with per-category threads, all queries used, and
        analysis prompts for downstream agents.
    """
    if categories is None:
        categories = list(PAIN_CATEGORIES.keys())

    category_results = {}
    queries_used = []

    for cat in categories:
        if cat not in PAIN_CATEGORIES:
            continue
        result = search_reddit_struggles(keywords, results_per_category, cat)
        category_results[cat] = result.get("threads", [])
        queries_used.append({"category": cat, "query": result.get("query_used", "")})

    # Flatten all threads for easy iteration
    all_threads = []
    for cat, threads in category_results.items():
        for thread in threads:
            thread["pain_category"] = cat
            all_threads.append(thread)

    return {
        "by_category": category_results,
        "all_threads": all_threads,
        "queries_used": queries_used,
        "total_threads": len(all_threads),
        "categories_searched": categories,
        "source": "reddit_mining",
        "analysis_guide": {
            "steps": [
                "1. Cluster complaints — group similar frustrations across threads",
                "2. Count frequency — problems mentioned by many people = larger market",
                "3. Note workarounds — DIY solutions = proof of willingness to pay",
                "4. Check recency — old complaints with no new solutions = stale market gap",
                "5. Find the quote — save vivid user quotes as future landing page copy",
            ],
        },
    }


###############################################################################
# Reddit Browser Helpers — Generate URLs and queries for Playwright MCP browsing
# Agents use Playwright tools (browser_navigate, browser_snapshot) to browse
# old.reddit.com directly, bypassing Google dork + WebFetch limitations.
###############################################################################

# Subreddit mappings by industry/domain
SUBREDDIT_MAP: Dict[str, List[str]] = {
    "legal": ["law", "LawFirm", "legaltech", "Lawyertalk", "LawSchool"],
    "healthcare": ["healthIT", "medicine", "nursing", "healthcare", "digitalhealth"],
    "fintech": ["fintech", "banking", "personalfinance", "CreditCards", "FinancialPlanning"],
    "saas": ["SaaS", "startups", "EntrepreneurRideAlong", "microsaas", "indiehackers"],
    "devtools": ["programming", "webdev", "devops", "softwaredevelopment", "coding"],
    "ai": ["artificial", "MachineLearning", "LocalLLaMA", "ChatGPT", "OpenAI"],
    "ecommerce": ["ecommerce", "shopify", "FulfillmentByAmazon", "Entrepreneur", "smallbusiness"],
    "education": ["edtech", "teaching", "education", "Teachers", "OnlineEducation"],
    "cybersecurity": ["cybersecurity", "netsec", "AskNetsec", "InfoSecNews", "hacking"],
    "hr": ["humanresources", "recruiting", "jobs", "careerguidance", "AskHR"],
    "marketing": ["marketing", "digital_marketing", "SEO", "socialmedia", "PPC"],
    "realestate": ["realestate", "RealEstateTechnology", "CommercialRealEstate", "PropertyManagement"],
    "construction": ["Construction", "Contractors", "ProjectManagement"],
    "accounting": ["Accounting", "tax", "Bookkeeping", "taxpros"],
    "insurance": ["Insurance", "InsuranceProfessional", "HealthInsurance"],
}


def suggest_subreddits(industry: str, problem_keywords: List[str] = None) -> List[str]:
    """
    Map an industry domain to relevant subreddits for targeted Reddit browsing.

    Args:
        industry: Industry or domain (e.g., "legal", "saas", "healthcare")
        problem_keywords: Optional additional keywords to find niche subreddits

    Returns:
        List of subreddit names (without r/ prefix) relevant to the industry
    """
    industry_lower = industry.lower()
    subreddits = []

    # Direct match
    if industry_lower in SUBREDDIT_MAP:
        subreddits.extend(SUBREDDIT_MAP[industry_lower])

    # Partial match — check if industry keyword appears in any map key
    for key, subs in SUBREDDIT_MAP.items():
        if key in industry_lower or industry_lower in key:
            for sub in subs:
                if sub not in subreddits:
                    subreddits.append(sub)

    # Always include general startup/business subreddits for B2B problems
    general_subs = ["startups", "Entrepreneur", "smallbusiness"]
    for sub in general_subs:
        if sub not in subreddits:
            subreddits.append(sub)

    return subreddits[:10]  # Cap at 10 to keep browsing manageable


def build_reddit_search_query(keywords: List[str], pain_category: Optional[str] = None) -> str:
    """
    Build a Reddit-native search query string optimized for Reddit's internal
    search engine (not Google dork). Uses quoted phrases and OR operators.

    Args:
        keywords: Topic keywords (e.g., ["legal research", "small law firms"])
        pain_category: Optional pain category to target. One of:
            "usability", "failure", "trust", "cost", "gaps".
            If None, builds a broad query.

    Returns:
        Query string for Reddit's internal search (used in URL param q=)
    """
    # Topic part — OR together quoted phrases
    topic_parts = [f'"{kw}"' for kw in keywords[:3]]
    topic = " OR ".join(topic_parts)

    if pain_category and pain_category in PAIN_CATEGORIES:
        # Pick top 3 pain words for the category (Reddit search is less powerful than Google)
        pain_words = PAIN_CATEGORIES[pain_category][:3]
        pain_part = " OR ".join(f'"{pw}"' for pw in pain_words)
        return f"({topic}) ({pain_part})"

    return topic


def build_reddit_search_urls(
    keywords: List[str],
    subreddits: Optional[List[str]] = None,
    categories: Optional[List[str]] = None,
    time_filter: str = "year",
) -> List[Dict[str, str]]:
    """
    Generate old.reddit.com search URLs for each pain category, ready for
    Playwright browser_navigate. Uses old.reddit.com because it's server-rendered
    HTML that works reliably with browser_snapshot.

    Args:
        keywords: Topic keywords (e.g., ["legal research", "small law firms"])
        subreddits: Optional specific subreddits to search within.
            If provided, generates subreddit-restricted searches.
        categories: Pain categories to generate URLs for.
            Defaults to all: ["usability", "failure", "trust", "cost", "gaps"].
        time_filter: Reddit time filter. One of: "hour", "day", "week",
            "month", "year", "all". Default "year".

    Returns:
        List of dicts with keys: url, category, query, subreddit (if restricted)
    """
    if categories is None:
        categories = list(PAIN_CATEGORIES.keys())

    urls = []

    for category in categories:
        if category not in PAIN_CATEGORIES:
            continue

        query = build_reddit_search_query(keywords, category)
        encoded_query = requests.utils.quote(query)

        if subreddits:
            # Subreddit-restricted searches
            for sub in subreddits[:5]:
                url = (
                    f"https://old.reddit.com/r/{sub}/search"
                    f"?q={encoded_query}&restrict_sr=on&sort=relevance&t={time_filter}"
                )
                urls.append({
                    "url": url,
                    "category": category,
                    "query": query,
                    "subreddit": sub,
                })
        else:
            # Global Reddit search
            url = (
                f"https://old.reddit.com/search"
                f"?q={encoded_query}&sort=relevance&t={time_filter}"
            )
            urls.append({
                "url": url,
                "category": category,
                "query": query,
                "subreddit": None,
            })

    return urls


###############################################################################
# Review Mining — Surface ideas from 2-3 star reviews on G2, Capterra, etc.
# 2-3 star reviewers are committed users hitting real, recurring limitations.
# Their complaints are specific, actionable, and shared by silent users.
###############################################################################

REVIEW_COMPLAINT_KEYWORDS: List[str] = [
    "wish", "but", "except", "missing", "would be perfect if",
    "deal breaker", "switched from", "almost good enough",
    "not enough", "too limited", "frustrating",
]

REVIEW_COMPLAINT_BUCKETS: Dict[str, List[str]] = {
    "missing_feature": [
        "missing feature", "doesn't have", "no support for",
        "wish it had", "need", "lacking",
    ],
    "bad_ux": [
        "confusing", "clunky", "not intuitive", "hard to use",
        "bad UX", "poor interface", "too many clicks",
    ],
    "pricing_mismatch": [
        "too expensive", "not worth the price", "overpriced",
        "cheaper alternative", "free tier", "hidden fees",
    ],
    "integration_gaps": [
        "doesn't integrate", "no API", "can't connect",
        "missing integration", "incompatible", "doesn't work with",
    ],
    "performance": [
        "slow", "crashes", "buggy", "unreliable", "downtime",
        "laggy", "performance issues",
    ],
}


def mine_review_platforms(
    product_keywords: List[str],
    platforms: Optional[List[str]] = None,
    results_per_query: int = 8,
) -> Dict:
    """
    Mine 2-3 star reviews from G2, Capterra, App Store and similar platforms.

    Targets the sweet spot: users who care enough to stay but are frustrated
    enough to complain. Their complaints map directly to startup opportunities.

    Args:
        product_keywords: Product or category keywords (e.g. ["project management", "CRM"])
        platforms: Review platforms to search. Defaults to G2, Capterra, TrustRadius,
                   App Store, ProductHunt.
        results_per_query: Results per search query (default 8)

    Returns:
        Dict with categorized review complaints, queries used, and analysis guide
    """
    if platforms is None:
        platforms = ["g2.com", "capterra.com", "trustradius.com",
                     "producthunt.com", "apps.apple.com"]

    topic = " OR ".join(f'"{kw}"' for kw in product_keywords)
    complaint_terms = " OR ".join(f'"{t}"' for t in REVIEW_COMPLAINT_KEYWORDS[:6])

    all_results = {}
    queries_used = []

    # Search each platform for 2-3 star style complaints
    for platform in platforms:
        query = f'{topic} site:{platform} ({complaint_terms}) review'
        results = search_web(query, results_per_query)
        platform_key = platform.split(".")[0]
        all_results[platform_key] = results.get("organic", [])
        queries_used.append({"platform": platform, "query": query})

    # Search by complaint bucket across all platforms
    bucket_results = {}
    for bucket, terms in REVIEW_COMPLAINT_BUCKETS.items():
        bucket_terms = " OR ".join(f'"{t}"' for t in terms[:4])
        query = f'{topic} ({bucket_terms}) review'
        results = search_web(query, results_per_query)
        bucket_results[bucket] = results.get("organic", [])
        queries_used.append({"bucket": bucket, "query": query})

    # Cross-platform complaint search (most valuable — shared category pain)
    cross_query = f'{topic} "switched from" OR "moved to" OR "alternative" review comparison'
    cross_results = search_web(cross_query, results_per_query)

    return {
        "by_platform": all_results,
        "by_complaint_bucket": bucket_results,
        "cross_platform": cross_results.get("organic", []),
        "queries_used": queries_used,
        "source": "review_mining",
        "analysis_guide": {
            "complaint_buckets": {
                "missing_feature": "Build the feature as a standalone tool or plugin",
                "bad_ux": "Rebuild the workflow from scratch for a specific persona",
                "pricing_mismatch": "Repackage for an underserved segment (freelancers, SMBs)",
                "integration_gaps": "Build the bridge product or all-in-one for that niche",
                "performance": "Rebuild with modern infra for the segment that cares most",
            },
            "steps": [
                "1. Categorize each complaint into a bucket (feature, UX, pricing, integration, performance)",
                "2. Count frequency — same complaint across multiple products = category gap",
                "3. Cross-reference with Reddit/Twitter to confirm pain exists outside reviews",
                "4. For each high-frequency complaint, identify: WHO says it (persona), WHAT they switch to (competitor), WHAT perfect looks like (landing page copy)",
                "5. Prioritize complaints from 2-3 star reviews — these are committed users, not rage-quitters",
            ],
        },
    }


###############################################################################
# Twitter Feed Ideation — Extract startup ideas from builders' public thinking
# Builders narrate their problem-solving process publicly. Every complaint is
# a customer discovery interview they didn't know they were giving.
###############################################################################

BUILDER_SIGNAL_QUERIES: Dict[str, str] = {
    "frustrations": '"{handle}" ("why is" OR "so hard" OR "frustrated" OR "broken" OR "wish")',
    "building": '"{handle}" ("building" OR "shipped" OR "launched" OR "working on" OR "side project")',
    "requests": '"{handle}" ("has anyone built" OR "looking for" OR "need a tool" OR "someone should")',
    "pricing_ux": '"{handle}" ("changed pricing" OR "new pricing" OR "redesigned" OR "pivot")',
    "investing": '"{handle}" ("invested in" OR "advising" OR "angel" OR "bet on")',
    "predictions": '"{handle}" ("2026" OR "next year" OR "future of" OR "betting on" OR "thesis")',
}


def mine_builder_twitter_feed(
    handle: str,
    num_results: int = 10,
    signal_types: Optional[List[str]] = None,
) -> Dict:
    """
    Analyze a builder's Twitter/X feed for startup idea signals.

    Extracts patterns from their public thinking: what they build, what
    frustrates them, what they keep talking about, and where they see gaps.

    Args:
        handle: Twitter handle (with or without @)
        num_results: Results per signal query (default 10)
        signal_types: Which signals to mine. Defaults to all:
            frustrations, building, requests, pricing_ux, investing, predictions

    Returns:
        Dict with signals by type, queries used, and idea generation guide
    """
    handle = handle.lstrip("@")

    if signal_types is None:
        signal_types = list(BUILDER_SIGNAL_QUERIES.keys())

    signals = {}
    queries_used = []

    for signal_type in signal_types:
        if signal_type not in BUILDER_SIGNAL_QUERIES:
            continue
        template = BUILDER_SIGNAL_QUERIES[signal_type]
        query = template.format(handle=handle)
        # Try X-native search first, fall back to web
        x_query = f"from:{handle} " + {
            "frustrations": '"why is" OR "so hard" OR "frustrated" OR "broken"',
            "building": '"building" OR "shipped" OR "launched" OR "working on"',
            "requests": '"has anyone built" OR "looking for" OR "need a tool"',
            "pricing_ux": '"pricing" OR "redesigned" OR "pivot"',
            "investing": '"invested in" OR "advising" OR "angel"',
            "predictions": '"2026" OR "future of" OR "betting on" OR "thesis"',
        }.get(signal_type, "")

        x_results = search_x_twitter(x_query, num_results)
        web_results = search_web(
            f"site:twitter.com OR site:x.com {query}", num_results
        )

        signals[signal_type] = {
            "x_native": x_results.get("tweets", x_results.get("twitter_posts", [])),
            "web_results": web_results.get("organic", []),
        }
        queries_used.append({"signal_type": signal_type, "query": query})

    return {
        "handle": handle,
        "signals": signals,
        "queries_used": queries_used,
        "source": "twitter_feed_ideation",
        "analysis_guide": {
            "signal_interpretation": {
                "built_a_tool": "The problem was painful enough to spend months on — others feel it too",
                "complains_about_X": "Unsolved problem, potentially underserved market",
                "changed_pricing_ux": "Old model was broken — the category likely has the same issue",
                "asks_has_anyone_built": "Open whitespace they've validated but not pursued",
                "invests_in_category": "They see momentum before the market does",
            },
            "idea_generation": [
                "Go deeper — solve the root cause they're patching around",
                "Go wider — does their frustration apply to adjacent markets/personas?",
                "Go meta — build the infrastructure THEY needed to build their thing",
                "Go opposite — are they wrong? Contrarian takes = contrarian startups",
            ],
            "ranking_criteria": [
                "Conviction strength: mentioned once vs obsessed for months",
                "Gap clarity: well-defined problem or vague frustration?",
                "Build vs buy: would their audience pay or build it themselves?",
            ],
        },
    }


###############################################################################
# Competitor Churn Mining — Find ideas from users actively leaving products
# Churning users are pre-qualified: they've paid, used deeply, and decided
# to leave. This is the highest-intent signal you can mine.
###############################################################################

CHURN_QUERY_TEMPLATES: Dict[str, str] = {
    "alternatives": '"alternatives to {product}" site:reddit.com',
    "switched_from": '"switched from {product} to" site:reddit.com',
    "cancelling": '("cancelled {product}" OR "canceling {product}" OR "canceled {product}")',
    "leaving": '("done with {product}" OR "leaving {product}" OR "left {product}")',
    "migration": '"{product} vs" OR "{product} alternative" OR "replacing {product}"',
    "segment_specific": '"{product} alternative" ("for small team" OR "for freelancers" OR "for startups" OR "self-hosted")',
}

CHURN_REASON_BUCKETS: Dict[str, str] = {
    "price_increase": "Build for the segment they abandoned (freelancers, small teams)",
    "missing_feature": "Build a focused product that nails that one thing",
    "complexity_bloat": "Build the simpler version for a specific persona",
    "bad_support": "Same product, better relationship (white-glove for a niche)",
    "acquired_sunset": "Orphaned users with no home — direct replacement play",
    "platform_shift": "Build native for the ecosystem they're moving to",
}


def mine_competitor_churn(
    competitor_names: List[str],
    results_per_query: int = 8,
) -> Dict:
    """
    Mine churn signals for competitors — find users actively leaving products.

    Targets the highest-intent signal: people who paid, used deeply, and
    decided to switch. Their reasons map directly to startup opportunities.

    Args:
        competitor_names: List of competitor product names (e.g. ["Notion", "Asana"])
        results_per_query: Results per search query (default 8)

    Returns:
        Dict with churn signals per competitor, migration paths, and analysis guide
    """
    competitor_churn = {}
    queries_used = []

    for product in competitor_names:
        product_signals = {}

        for signal_type, template in CHURN_QUERY_TEMPLATES.items():
            query = template.format(product=product)
            results = search_web(query, results_per_query)
            product_signals[signal_type] = results.get("organic", [])
            queries_used.append({
                "product": product,
                "signal_type": signal_type,
                "query": query,
            })

        competitor_churn[product] = product_signals

    # Cross-competitor: search for category-wide churn (strongest signal)
    if len(competitor_names) >= 2:
        category_query = " OR ".join(
            f'"alternative to {p}"' for p in competitor_names[:5]
        )
        category_results = search_web(
            f"({category_query}) site:reddit.com", results_per_query
        )
    else:
        category_results = {"organic": []}

    # Google Trends for "[product] alternative" — rising = growing churn wave
    trends_queries = {}
    for product in competitor_names[:3]:
        trend_query = f'"{product} alternative" trends interest'
        trends_queries[product] = search_web(trend_query, 5).get("organic", [])

    return {
        "by_competitor": competitor_churn,
        "category_wide_churn": category_results.get("organic", []),
        "alternative_trends": trends_queries,
        "queries_used": queries_used,
        "source": "churn_mining",
        "analysis_guide": {
            "churn_reason_opportunities": CHURN_REASON_BUCKETS,
            "steps": [
                "1. Categorize each churn reason (price, feature, complexity, support, sunset, platform)",
                "2. Map migration paths: where are they going, where NOT going (= gaps), what they settle for",
                "3. Validate scale: same churn pattern across 3-5 competitors = category problem, not product problem",
                "4. Check Google Trends for '[product] alternative' — rising = growing churn wave",
                "5. Look for cobbled-together solutions (spreadsheets, Zapier chains) = unbundling opportunity",
            ],
        },
    }


def search_customer_pain_points(problem: str, industry: str = None) -> Dict:
    """
    Search for customer pain points and complaints.

    Args:
        problem: Problem statement or topic
        industry: Industry context (optional)

    Returns:
        Dict with pain point data from forums, reviews, and Reddit threads
    """
    queries = [
        f"{problem} challenges problems",
        f"{problem} complaints issues reddit",
        f"{problem} customer feedback reviews"
    ]

    if industry:
        queries = [f"{industry} {q}" for q in queries]

    # Build keyword list for Reddit deep search
    reddit_keywords = [problem]
    if industry:
        reddit_keywords.append(industry)

    results = {
        "challenges": search_web(queries[0], 10),
        "complaints": search_web(queries[1], 10),
        "feedback": search_web(queries[2], 10),
        "reddit_mining": mine_reddit_pain_points(reddit_keywords)
    }

    return results


def search_technology_stack(product_type: str) -> Dict:
    """
    Search for technology recommendations and stack info.

    Args:
        product_type: Type of product to build

    Returns:
        Dict with technology recommendations
    """
    queries = [
        f"how to build {product_type} tech stack",
        f"{product_type} architecture best practices",
        f"{product_type} open source frameworks libraries"
    ]

    results = {
        "tech_stack": search_web(queries[0], 10),
        "architecture": search_web(queries[1], 10),
        "frameworks": search_web(queries[2], 10)
    }

    return results


def search_google_trends(keywords: List[str], timeframe: str = "today 12-m") -> Dict:
    """
    Search for Google Trends data on keywords.

    Args:
        keywords: List of keywords to analyze (max 5)
        timeframe: Time range - "today 12-m", "today 3-m", "today 5-y"

    Returns:
        Dict with trends data including interest over time and related queries
    """
    results = {}

    for keyword in keywords[:5]:  # Google Trends limits to 5 keywords
        # Search for Google Trends data via web search
        trends_query = f"Google Trends {keyword} interest over time"
        trends_results = search_web(trends_query, 5)

        # Search for related trending topics
        related_query = f"{keyword} trending topics 2024 2025"
        related_results = search_web(related_query, 5)

        # Search for "rising" queries related to keyword
        rising_query = f"{keyword} rising searches emerging trends"
        rising_results = search_web(rising_query, 5)

        results[keyword] = {
            "trends_data": trends_results.get("organic", []),
            "related_topics": related_results.get("organic", []),
            "rising_queries": rising_results.get("organic", []),
            "answer_box": trends_results.get("answerBox", {})
        }

    return results


def search_google_trends_comparison(keywords: List[str]) -> Dict:
    """
    Compare multiple keywords on Google Trends.

    Args:
        keywords: List of keywords to compare (max 5)

    Returns:
        Dict with comparison data
    """
    keywords_str = " vs ".join(keywords[:5])
    query = f"Google Trends {keywords_str} comparison"

    results = search_web(query, 10)

    return {
        "comparison": results.get("organic", []),
        "keywords": keywords[:5],
        "answer_box": results.get("answerBox", {})
    }


def search_x_twitter(query: str, num_results: int = 20) -> Dict:
    """
    Search for X (Twitter) posts and discussions.

    Uses X API if bearer token available, otherwise searches via web.

    Args:
        query: Search query
        num_results: Number of results

    Returns:
        Dict with X/Twitter posts and engagement data
    """
    if X_BEARER_TOKEN:
        # Use X API v2
        return _search_x_api(query, num_results)
    else:
        # Fall back to web search for Twitter content
        return _search_x_web(query, num_results)


def _search_x_api(query: str, num_results: int = 20, timeout: int = DEFAULT_TIMEOUT) -> Dict:
    """
    Search X using the official API with timeout and error handling.

    Args:
        query: Search query
        num_results: Max results (10-100)
        timeout: Request timeout in seconds (default 30)

    Returns:
        Dict with tweets and metadata
    """
    headers = {
        "Authorization": f"Bearer {X_BEARER_TOKEN}",
        "Content-Type": "application/json"
    }

    # X API v2 recent search endpoint
    url = "https://api.twitter.com/2/tweets/search/recent"
    params = {
        "query": query,
        "max_results": min(num_results, 100),
        "tweet.fields": "created_at,public_metrics,author_id,conversation_id",
        "expansions": "author_id",
        "user.fields": "name,username,verified,public_metrics"
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=timeout)
        response.raise_for_status()
        data = response.json()

        tweets = data.get("data", [])
        users = {u["id"]: u for u in data.get("includes", {}).get("users", [])}

        # Enrich tweets with user data
        enriched_tweets = []
        for tweet in tweets:
            author = users.get(tweet.get("author_id"), {})
            enriched_tweets.append({
                "text": tweet.get("text"),
                "created_at": tweet.get("created_at"),
                "metrics": tweet.get("public_metrics", {}),
                "author": {
                    "name": author.get("name"),
                    "username": author.get("username"),
                    "verified": author.get("verified", False),
                    "followers": author.get("public_metrics", {}).get("followers_count", 0)
                }
            })

        return {
            "source": "x_api",
            "tweets": enriched_tweets,
            "result_count": len(enriched_tweets),
            "query": query
        }

    except requests.Timeout:
        return {"error": f"X API timed out after {timeout}s", "source": "x_api", "tweets": []}
    except requests.HTTPError as e:
        return {"error": f"X API HTTP error: {e.response.status_code}", "source": "x_api", "tweets": []}
    except requests.RequestException as e:
        return {"error": f"X API request failed: {str(e)}", "source": "x_api", "tweets": []}


def _search_x_web(query: str, num_results: int = 20) -> Dict:
    """
    Search for X/Twitter content via web search.

    Args:
        query: Search query
        num_results: Number of results

    Returns:
        Dict with Twitter-related web results
    """
    # Search Twitter/X specific content
    twitter_query = f"site:twitter.com OR site:x.com {query}"
    twitter_results = search_web(twitter_query, num_results)

    # Search for Twitter discussions about the topic
    discussion_query = f"{query} twitter discussion thread"
    discussion_results = search_web(discussion_query, 10)

    # Search for viral tweets about the topic
    viral_query = f"{query} viral tweet popular"
    viral_results = search_web(viral_query, 10)

    return {
        "source": "web_search",
        "twitter_posts": twitter_results.get("organic", []),
        "discussions": discussion_results.get("organic", []),
        "viral_content": viral_results.get("organic", []),
        "query": query
    }


def search_social_sentiment(topic: str) -> Dict:
    """
    Search for social media sentiment and discussions about a topic.

    Args:
        topic: Topic to analyze

    Returns:
        Dict with sentiment indicators from X, Reddit, and other sources
    """
    # X/Twitter sentiment
    x_results = search_x_twitter(f"{topic} -filter:retweets", 20)

    # Reddit discussions
    reddit_query = f"site:reddit.com {topic}"
    reddit_results = search_web(reddit_query, 15)

    # General social buzz
    social_query = f"{topic} social media reaction opinions"
    social_results = search_web(social_query, 10)

    # News sentiment
    news_query = f"{topic} news reaction response"
    news_results = search_web(news_query, 10)

    return {
        "x_twitter": x_results,
        "reddit": reddit_results.get("organic", []),
        "social_buzz": social_results.get("organic", []),
        "news_sentiment": news_results.get("organic", []),
        "topic": topic
    }


def search_market_signals(industry: str, keywords: List[str] = None) -> Dict:
    """
    Comprehensive market signal search combining trends, social, and news.

    Args:
        industry: Industry to research
        keywords: Additional keywords

    Returns:
        Dict with comprehensive market signals
    """
    all_keywords = [industry] + (keywords or [])

    return {
        "google_trends": search_google_trends(all_keywords[:3]),
        "social_sentiment": search_social_sentiment(industry),
        "market_data": search_market_data(industry, keywords),
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    # Test the functions
    print("Testing web research functions...")

    # Example: Search for AI cost management market
    market_data = search_market_data("AI cost management", ["enterprise", "FinOps"])
    print(f"Found {len(market_data.get('market_size', {}).get('organic', []))} market size results")

    # Test Google Trends
    print("\nTesting Google Trends search...")
    trends = search_google_trends(["AI coding assistant", "developer productivity"])
    print(f"Found trends data for {len(trends)} keywords")

    # Test X/Twitter search
    print("\nTesting X/Twitter search...")
    x_results = search_x_twitter("AI developer tools")
    print(f"Source: {x_results.get('source')}")
    print(f"Found {len(x_results.get('twitter_posts', x_results.get('tweets', [])))} results")
