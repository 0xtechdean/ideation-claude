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


def search_customer_pain_points(problem: str, industry: str = None) -> Dict:
    """
    Search for customer pain points and complaints.

    Args:
        problem: Problem statement or topic
        industry: Industry context (optional)

    Returns:
        Dict with pain point data from forums, reviews, etc.
    """
    queries = [
        f"{problem} challenges problems",
        f"{problem} complaints issues reddit",
        f"{problem} customer feedback reviews"
    ]

    if industry:
        queries = [f"{industry} {q}" for q in queries]

    results = {
        "challenges": search_web(queries[0], 10),
        "complaints": search_web(queries[1], 10),
        "feedback": search_web(queries[2], 10)
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
