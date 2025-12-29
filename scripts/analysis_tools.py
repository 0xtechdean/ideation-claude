"""
Analysis Tools for Ideation Agents
Reusable functions for market analysis, scoring, and competitive analysis
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class ScoreWeight(Enum):
    """Scoring criteria weights."""
    PROBLEM_SEVERITY = 0.25
    MARKET_SIZE = 0.25
    WILLINGNESS_TO_PAY = 0.25
    SOLUTION_FIT = 0.25


@dataclass
class MarketSize:
    """Market size data structure."""
    tam: float  # Total Addressable Market
    sam: float  # Serviceable Addressable Market
    som: float  # Serviceable Obtainable Market
    tam_description: str = ""
    sam_description: str = ""
    som_description: str = ""
    growth_rate: float = 0.0
    projection_year: int = 2030


def calculate_tam_sam_som(
    total_market: float,
    serviceable_percent: float = 0.30,
    obtainable_percent: float = 0.01,
    growth_rate: float = 0.15
) -> MarketSize:
    """
    Calculate TAM/SAM/SOM from total market size.

    Args:
        total_market: Total addressable market in dollars
        serviceable_percent: Percent of TAM that is serviceable (default 30%)
        obtainable_percent: Percent of SAM that is obtainable (default 1%)
        growth_rate: Annual growth rate (default 15%)

    Returns:
        MarketSize dataclass with calculated values
    """
    tam = total_market
    sam = tam * serviceable_percent
    som = sam * obtainable_percent

    return MarketSize(
        tam=tam,
        sam=sam,
        som=som,
        growth_rate=growth_rate
    )


def format_market_size(amount: float) -> str:
    """Format a market size number for display."""
    if amount >= 1_000_000_000:
        return f"${amount / 1_000_000_000:.1f}B"
    elif amount >= 1_000_000:
        return f"${amount / 1_000_000:.1f}M"
    elif amount >= 1_000:
        return f"${amount / 1_000:.1f}K"
    else:
        return f"${amount:.0f}"


def score_criteria(
    criteria_scores: Dict[str, float],
    weights: Dict[str, float] = None
) -> Tuple[float, Dict[str, float]]:
    """
    Calculate weighted score from multiple criteria.

    Args:
        criteria_scores: Dict mapping criteria names to scores (0-10)
        weights: Dict mapping criteria names to weights (should sum to 1.0)

    Returns:
        Tuple of (final_score, weighted_scores_breakdown)
    """
    if weights is None:
        # Default equal weights
        weights = {k: 1.0 / len(criteria_scores) for k in criteria_scores}

    weighted_scores = {}
    total_weighted = 0.0

    for criterion, score in criteria_scores.items():
        weight = weights.get(criterion, 0)
        weighted = score * weight
        weighted_scores[criterion] = weighted
        total_weighted += weighted

    return total_weighted, weighted_scores


def calculate_combined_score(problem_score: float, solution_score: float) -> float:
    """
    Calculate combined score with standard weighting.

    Args:
        problem_score: Problem validation score (0-10)
        solution_score: Solution validation score (0-10)

    Returns:
        Combined weighted score
    """
    return (problem_score * 0.6) + (solution_score * 0.4)


def evaluate_score_decision(score: float, threshold: float = 5.0) -> str:
    """
    Determine pass/fail decision based on score.

    Args:
        score: Score to evaluate
        threshold: Passing threshold (default 5.0)

    Returns:
        'pass' or 'fail' string
    """
    return "pass" if score >= threshold else "fail"


@dataclass
class Competitor:
    """Competitor data structure."""
    name: str
    description: str
    funding: str = ""
    strengths: List[str] = None
    weaknesses: List[str] = None
    pricing: str = ""
    target_market: str = ""


def generate_competitive_matrix(competitors: List[Competitor]) -> Dict:
    """
    Generate a competitive analysis matrix.

    Args:
        competitors: List of Competitor objects

    Returns:
        Dict with competitive matrix data
    """
    matrix = {
        "competitors": [],
        "comparison_criteria": [
            "pricing",
            "features",
            "target_market",
            "funding",
            "market_position"
        ]
    }

    for comp in competitors:
        matrix["competitors"].append({
            "name": comp.name,
            "description": comp.description,
            "funding": comp.funding,
            "strengths": comp.strengths or [],
            "weaknesses": comp.weaknesses or [],
            "pricing": comp.pricing,
            "target_market": comp.target_market
        })

    return matrix


def identify_market_gaps(
    competitors: List[Competitor],
    market_needs: List[str]
) -> List[Dict]:
    """
    Identify gaps in the market based on competitor analysis.

    Args:
        competitors: List of competitors
        market_needs: List of identified market needs

    Returns:
        List of market gap opportunities
    """
    gaps = []

    # Collect all competitor weaknesses
    all_weaknesses = []
    for comp in competitors:
        if comp.weaknesses:
            all_weaknesses.extend(comp.weaknesses)

    # Find needs that align with weaknesses
    for need in market_needs:
        need_lower = need.lower()
        matching_weaknesses = [
            w for w in all_weaknesses
            if any(word in w.lower() for word in need_lower.split())
        ]

        if matching_weaknesses:
            gaps.append({
                "need": need,
                "competitor_weaknesses": matching_weaknesses,
                "opportunity_size": "medium" if len(matching_weaknesses) < 3 else "large"
            })

    return gaps


@dataclass
class CustomerSegment:
    """Customer segment data structure."""
    name: str
    size: str
    budget: str
    pain_points: List[str]
    buying_criteria: List[str] = None
    decision_maker: str = ""


def create_customer_segments(
    segment_data: List[Dict]
) -> List[CustomerSegment]:
    """
    Create customer segment objects from raw data.

    Args:
        segment_data: List of dicts with segment info

    Returns:
        List of CustomerSegment objects
    """
    segments = []
    for data in segment_data:
        segments.append(CustomerSegment(
            name=data.get("name", ""),
            size=data.get("size", ""),
            budget=data.get("budget", ""),
            pain_points=data.get("pain_points", []),
            buying_criteria=data.get("buying_criteria", []),
            decision_maker=data.get("decision_maker", "")
        ))
    return segments


@dataclass
class MVPFeature:
    """MVP feature data structure."""
    name: str
    description: str
    priority: int  # 1 = highest
    complexity: str  # low, medium, high
    time_estimate: str = ""


def prioritize_mvp_features(features: List[MVPFeature]) -> List[MVPFeature]:
    """
    Sort MVP features by priority and complexity.

    Args:
        features: List of MVPFeature objects

    Returns:
        Sorted list with highest priority, lowest complexity first
    """
    complexity_order = {"low": 0, "medium": 1, "high": 2}

    return sorted(
        features,
        key=lambda f: (f.priority, complexity_order.get(f.complexity, 1))
    )


def generate_scoring_rubric() -> Dict:
    """
    Generate the standard scoring rubric for evaluation.

    Returns:
        Dict with scoring criteria and descriptions
    """
    return {
        "problem_severity": {
            "weight": 0.25,
            "scale": "1-10",
            "description": "How severe is the problem for the target customer?",
            "scoring_guide": {
                "1-3": "Nice-to-have, not urgent",
                "4-6": "Important but not critical",
                "7-8": "Significant pain, actively seeking solutions",
                "9-10": "Critical problem, must solve immediately"
            }
        },
        "market_size": {
            "weight": 0.25,
            "scale": "1-10",
            "description": "How large is the addressable market?",
            "scoring_guide": {
                "1-3": "Niche market < $100M",
                "4-6": "Medium market $100M-$1B",
                "7-8": "Large market $1B-$10B",
                "9-10": "Massive market > $10B"
            }
        },
        "willingness_to_pay": {
            "weight": 0.25,
            "scale": "1-10",
            "description": "Are customers willing and able to pay?",
            "scoring_guide": {
                "1-3": "Free alternatives exist, low budget",
                "4-6": "Some budget, price sensitive",
                "7-8": "Clear budget, proven willingness",
                "9-10": "Urgent need, budget allocated"
            }
        },
        "solution_fit": {
            "weight": 0.25,
            "scale": "1-10",
            "description": "How well does the solution address the problem?",
            "scoring_guide": {
                "1-3": "Partial solution, many gaps",
                "4-6": "Decent fit, some improvements needed",
                "7-8": "Strong fit, minor adjustments",
                "9-10": "Perfect fit, clear differentiation"
            }
        },
        "technical_viability": {
            "weight": 0,  # Not weighted, informational
            "scale": "1-10",
            "description": "How feasible is the technical implementation?"
        },
        "competitive_advantage": {
            "weight": 0,  # Not weighted, informational
            "scale": "1-10",
            "description": "How defensible is the competitive position?"
        },
        "resource_requirements": {
            "weight": 0,  # Not weighted, informational
            "scale": "1-10",
            "description": "How reasonable are the resource requirements?"
        },
        "time_to_market": {
            "weight": 0,  # Not weighted, informational
            "scale": "1-10",
            "description": "How quickly can an MVP be delivered?"
        }
    }


if __name__ == "__main__":
    # Test the functions
    print("Testing analysis tools...")

    # Test TAM/SAM/SOM calculation
    market = calculate_tam_sam_som(4_200_000_000)
    print(f"TAM: {format_market_size(market.tam)}")
    print(f"SAM: {format_market_size(market.sam)}")
    print(f"SOM: {format_market_size(market.som)}")

    # Test scoring
    scores = {
        "problem_severity": 8,
        "market_size": 7,
        "willingness_to_pay": 6,
        "solution_fit": 7
    }
    weights = {
        "problem_severity": 0.25,
        "market_size": 0.25,
        "willingness_to_pay": 0.25,
        "solution_fit": 0.25
    }
    final_score, breakdown = score_criteria(scores, weights)
    print(f"Final Score: {final_score}")
    print(f"Decision: {evaluate_score_decision(final_score)}")
