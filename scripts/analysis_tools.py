"""
Analysis Tools for Ideation Agents
Reusable functions for market analysis, scoring, and competitive analysis

v2.0 - Updated scoring model with:
- Kill switch gates (competitor, regulatory, timing)
- Split Problem Severity into Pain Severity + Startup Addressability
- Market Timing as standalone criterion
- Competitive Advantage floor (≤3 = auto-fail)
- WTP evidence tiers
- Smart mediocrity check for marginal passes
- 55/45 problem/solution weighting
"""

from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum


# --- Kill Switch System ---

class KillSwitchResult(Enum):
    """Kill switch gate results."""
    CLEAR = "clear"
    TRIGGERED = "triggered"


@dataclass
class KillSwitch:
    """Result of a kill switch evaluation."""
    gate: str  # "competitor", "regulatory", "timing"
    result: KillSwitchResult
    reason: str
    evidence: str = ""

    @property
    def triggered(self) -> bool:
        return self.result == KillSwitchResult.TRIGGERED


def evaluate_kill_switches(
    competitor_kill: Optional[KillSwitch] = None,
    regulatory_kill: Optional[KillSwitch] = None,
    timing_kill: Optional[KillSwitch] = None,
) -> Tuple[bool, List[KillSwitch]]:
    """
    Evaluate all kill switch gates. Any triggered gate = AUTO-FAIL.

    Returns:
        Tuple of (any_triggered, list_of_all_switches)
    """
    switches = []
    any_triggered = False

    for switch in [competitor_kill, regulatory_kill, timing_kill]:
        if switch is not None:
            switches.append(switch)
            if switch.triggered:
                any_triggered = True

    return any_triggered, switches


def check_competitor_kill(
    exact_product_exists: bool,
    competitor_funding: float,  # in millions
    competitor_name: str = "",
    evidence: str = ""
) -> KillSwitch:
    """
    Check if a funded competitor already has the exact product.

    Triggers if: A competitor with $20M+ funding already built the exact product.
    """
    if exact_product_exists and competitor_funding >= 20:
        return KillSwitch(
            gate="competitor",
            result=KillSwitchResult.TRIGGERED,
            reason=f"{competitor_name} (${competitor_funding:.0f}M funded) already has the exact product",
            evidence=evidence
        )
    return KillSwitch(
        gate="competitor",
        result=KillSwitchResult.CLEAR,
        reason="No funded competitor with exact product identified"
    )


def check_regulatory_kill(
    core_feature_prohibited: bool,
    licensing_cost: float = 0,  # in dollars
    licensing_time_months: int = 0,
    regulation_name: str = "",
    evidence: str = ""
) -> KillSwitch:
    """
    Check if the core value proposition is legally prohibited or requires
    prohibitive licensing ($500K+ or 12+ months).
    """
    if core_feature_prohibited:
        return KillSwitch(
            gate="regulatory",
            result=KillSwitchResult.TRIGGERED,
            reason=f"Core value proposition prohibited by {regulation_name}",
            evidence=evidence
        )
    if licensing_cost >= 500_000 or licensing_time_months >= 12:
        return KillSwitch(
            gate="regulatory",
            result=KillSwitchResult.TRIGGERED,
            reason=f"Requires ${licensing_cost:,.0f} and {licensing_time_months} months for licensing ({regulation_name})",
            evidence=evidence
        )
    return KillSwitch(
        gate="regulatory",
        result=KillSwitchResult.CLEAR,
        reason="No regulatory prohibition identified"
    )


def check_timing_kill(
    market_penetration_percent: float,  # current market penetration
    paying_customers_exist: bool,
    years_to_meaningful_adoption: float = 0,
    evidence: str = ""
) -> KillSwitch:
    """
    Check if the market is too early (< 2% penetration, no paying customers today).
    """
    if market_penetration_percent < 2.0 and not paying_customers_exist:
        return KillSwitch(
            gate="timing",
            result=KillSwitchResult.TRIGGERED,
            reason=f"Market at {market_penetration_percent:.1f}% penetration with no paying customers today",
            evidence=evidence
        )
    if years_to_meaningful_adoption >= 3.0:
        return KillSwitch(
            gate="timing",
            result=KillSwitchResult.TRIGGERED,
            reason=f"Meaningful adoption {years_to_meaningful_adoption:.0f}+ years away",
            evidence=evidence
        )
    return KillSwitch(
        gate="timing",
        result=KillSwitchResult.CLEAR,
        reason="Market timing acceptable"
    )


# --- WTP Evidence Tiers ---

class WTPTier(Enum):
    """Willingness to Pay evidence quality tiers."""
    TIER_1 = "tier_1"  # Direct: signed LOIs, existing payments for identical product
    TIER_2 = "tier_2"  # Validated: interview pricing, competitor revenue for same product type
    TIER_3 = "tier_3"  # Adjacent: category spending only, survey data, analyst projections

    @property
    def max_score(self) -> int:
        """Maximum WTP score allowed for this tier."""
        if self == WTPTier.TIER_1:
            return 10
        elif self == WTPTier.TIER_2:
            return 7
        else:
            return 4

    @property
    def label(self) -> str:
        if self == WTPTier.TIER_1:
            return "Direct Evidence (LOIs, payments for identical product)"
        elif self == WTPTier.TIER_2:
            return "Validated (interviews, competitor revenue for same type)"
        else:
            return "Adjacent Only (category spend, surveys, projections)"


def cap_wtp_score(raw_score: float, tier: WTPTier) -> Tuple[float, Optional[str]]:
    """
    Cap WTP score based on evidence tier.

    Returns:
        Tuple of (capped_score, warning_if_capped)
    """
    max_allowed = tier.max_score
    if raw_score > max_allowed:
        return float(max_allowed), f"WTP capped from {raw_score} to {max_allowed} (evidence is {tier.label})"
    return float(raw_score), None


# --- Score Weights (v2.0) ---

class ScoreWeight(Enum):
    """Problem validation scoring criteria weights (v2.0 - 5 criteria)."""
    PAIN_SEVERITY = 0.20
    STARTUP_ADDRESSABILITY = 0.20
    MARKET_SIZE = 0.20
    WILLINGNESS_TO_PAY = 0.20
    MARKET_TIMING = 0.20


# Problem/Solution weighting
PROBLEM_WEIGHT = 0.55
SOLUTION_WEIGHT = 0.45
PASS_THRESHOLD = 6.0
COMPETITIVE_ADVANTAGE_FLOOR = 3  # ≤ this = auto-fail
MARKET_TIMING_ELIMINATION = 4    # < this = early elimination


# --- Market Size ---

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


# --- Scoring Engine ---

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
    Calculate combined score with v2.0 weighting (55/45).

    Args:
        problem_score: Problem validation score (0-10)
        solution_score: Solution validation score (0-10)

    Returns:
        Combined weighted score
    """
    return (problem_score * PROBLEM_WEIGHT) + (solution_score * SOLUTION_WEIGHT)


def evaluate_score_decision(
    score: float,
    threshold: float = PASS_THRESHOLD,
    kill_switches: List[KillSwitch] = None,
    competitive_advantage: float = None,
    market_timing: float = None,
) -> Tuple[str, str]:
    """
    Determine pass/fail decision with kill switch and floor checks.

    Args:
        score: Combined score to evaluate
        threshold: Passing threshold (default 6.0)
        kill_switches: List of kill switch results
        competitive_advantage: CA score for floor check
        market_timing: MT score for elimination check

    Returns:
        Tuple of (decision, reason)
    """
    # Check kill switches first
    if kill_switches:
        for ks in kill_switches:
            if ks.triggered:
                return "fail", f"KILL SWITCH [{ks.gate.upper()}]: {ks.reason}"

    # Check competitive advantage floor
    if competitive_advantage is not None and competitive_advantage <= COMPETITIVE_ADVANTAGE_FLOOR:
        return "fail", f"COMPETITIVE ADVANTAGE FLOOR: Score {competitive_advantage}/10 ≤ {COMPETITIVE_ADVANTAGE_FLOOR} (someone with $50M+ already built this)"

    # Check market timing elimination
    if market_timing is not None and market_timing < MARKET_TIMING_ELIMINATION:
        return "fail", f"MARKET TIMING ELIMINATION: Score {market_timing}/10 < {MARKET_TIMING_ELIMINATION} (market not ready)"

    # Standard threshold check
    if score >= threshold:
        # Smart mediocrity check for marginal passes
        if score < 6.5:
            return "marginal_pass", f"MARGINAL PASS ({score:.2f}/10) — requires smart mediocrity review"
        return "pass", f"PASS ({score:.2f}/10)"
    else:
        return "fail", f"FAIL ({score:.2f}/10 < {threshold})"


def smart_mediocrity_check(
    combined_score: float,
    competitive_advantage: float,
    wtp_tier: WTPTier,
    market_timing: float,
    strongest_competitor_funding_m: float = 0,
) -> Tuple[str, str]:
    """
    For marginal passes (6.0-6.5), apply the "would you invest $500K?" test.

    Checks for dressed-up 4.0s: ideas with strong problem scores
    masking fatal competitive/timing/WTP weaknesses.

    Returns:
        Tuple of (verdict, reasoning)
    """
    red_flags = []

    if competitive_advantage <= 5:
        red_flags.append(f"Competitive Advantage only {competitive_advantage}/10 — incumbents can replicate")

    if wtp_tier == WTPTier.TIER_3:
        red_flags.append("WTP evidence is Tier 3 (adjacent spending only, no direct validation)")

    if market_timing < 6:
        red_flags.append(f"Market Timing {market_timing}/10 — market may not be ready")

    if strongest_competitor_funding_m >= 50:
        red_flags.append(f"Strongest competitor has ${strongest_competitor_funding_m:.0f}M in funding")

    if len(red_flags) >= 3:
        return "fail", f"SMART MEDIOCRITY CHECK FAILED — {len(red_flags)} red flags: " + "; ".join(red_flags)
    elif len(red_flags) >= 2:
        return "conditional_pass", f"CONDITIONAL PASS — {len(red_flags)} concerns: " + "; ".join(red_flags)
    else:
        return "pass", f"Marginal pass sustained — {len(red_flags)} minor concern(s)"


# --- Score Validation ---

def validate_single_score(score: Union[int, float, None], criterion: str = "") -> Tuple[float, Optional[str]]:
    """
    Validate a single score is in 1-10 range.

    Args:
        score: Score to validate (can be None)
        criterion: Name of criterion (for error messages)

    Returns:
        Tuple of (validated_score, warning_message or None)
    """
    if score is None:
        return 5.0, f"Missing score for {criterion}, defaulting to 5.0"

    if not isinstance(score, (int, float)):
        return 5.0, f"Invalid type for {criterion} score: {type(score)}, defaulting to 5.0"

    if score < 1:
        return 1.0, f"{criterion} score {score} below minimum, clamped to 1"
    if score > 10:
        return 10.0, f"{criterion} score {score} above maximum, clamped to 10"

    return float(score), None


def validate_scores(scores: Dict[str, Union[float, None]]) -> Tuple[Dict[str, float], List[str]]:
    """
    Validate all scores are in 1-10 range.

    Args:
        scores: Dict of criterion -> score

    Returns:
        Tuple of (validated_scores, warnings)
    """
    validated = {}
    warnings = []

    for criterion, score in scores.items():
        valid_score, warning = validate_single_score(score, criterion)
        validated[criterion] = valid_score
        if warning:
            warnings.append(warning)

    return validated, warnings


def calculate_problem_score(scores: Dict[str, float]) -> Tuple[float, Dict[str, float]]:
    """
    Calculate the problem validation score from component scores (v2.0).

    Now includes 5 criteria with equal 20% weights:
    - pain_severity (how bad the problem is objectively)
    - startup_addressability (how viable for a new entrant NOW)
    - market_size
    - willingness_to_pay
    - market_timing

    Args:
        scores: Dict with keys matching the 5 criteria above

    Returns:
        Tuple of (final_score, weighted_breakdown)
    """
    weights = {
        "pain_severity": 0.20,
        "startup_addressability": 0.20,
        "market_size": 0.20,
        "willingness_to_pay": 0.20,
        "market_timing": 0.20,
    }

    # Validate scores first
    validated, warnings = validate_scores(scores)
    for warning in warnings:
        print(f"Warning: {warning}")

    # Calculate weighted score
    weighted = {}
    total = 0.0

    for criterion, weight in weights.items():
        score = validated.get(criterion, 5.0)
        weighted[criterion] = score * weight
        total += weighted[criterion]

    return total, weighted


def calculate_solution_score(scores: Dict[str, float]) -> float:
    """
    Calculate the solution validation score from component scores.

    Args:
        scores: Dict with keys: technical_viability, competitive_advantage,
                               resource_requirements, time_to_market

    Returns:
        Average of the 4 solution criteria
    """
    # Validate scores first
    validated, warnings = validate_scores(scores)
    for warning in warnings:
        print(f"Warning: {warning}")

    criteria = ["technical_viability", "competitive_advantage",
                "resource_requirements", "time_to_market"]

    total = sum(validated.get(c, 5.0) for c in criteria)
    return total / len(criteria)


# --- Full Evaluation Pipeline ---

@dataclass
class EvaluationResult:
    """Complete evaluation result with all checks."""
    problem_score: float
    solution_score: Optional[float]
    combined_score: float
    verdict: str  # "pass", "fail", "conditional_pass", "marginal_pass"
    reason: str
    kill_switches: List[KillSwitch] = field(default_factory=list)
    kill_switch_triggered: bool = False
    competitive_advantage_floor_hit: bool = False
    market_timing_eliminated: bool = False
    smart_mediocrity_result: Optional[str] = None
    wtp_tier: Optional[WTPTier] = None
    wtp_capped: bool = False


def run_full_evaluation(
    problem_scores: Dict[str, float],
    solution_scores: Optional[Dict[str, float]] = None,
    kill_switches: List[KillSwitch] = None,
    wtp_tier: WTPTier = WTPTier.TIER_2,
    strongest_competitor_funding_m: float = 0,
) -> EvaluationResult:
    """
    Run the complete evaluation pipeline with all v2.0 checks.

    Args:
        problem_scores: Dict with 5 problem criteria
        solution_scores: Dict with 4 solution criteria (None if early elimination)
        kill_switches: List of kill switch results
        wtp_tier: WTP evidence quality tier
        strongest_competitor_funding_m: Largest competitor's funding in millions

    Returns:
        EvaluationResult with full decision chain
    """
    result = EvaluationResult(
        problem_score=0.0,
        solution_score=None,
        combined_score=0.0,
        verdict="pending",
        reason="",
        kill_switches=kill_switches or [],
        wtp_tier=wtp_tier,
    )

    # Step 1: Check kill switches
    if kill_switches:
        any_triggered, _ = evaluate_kill_switches(*[
            ks for ks in kill_switches if ks is not None
        ][:3]) if len(kill_switches) <= 3 else evaluate_kill_switches()

        for ks in kill_switches:
            if ks.triggered:
                result.kill_switch_triggered = True
                result.verdict = "fail"
                result.reason = f"KILL SWITCH [{ks.gate.upper()}]: {ks.reason}"
                # Still calculate scores for the report
                p_score, _ = calculate_problem_score(problem_scores)
                result.problem_score = p_score
                result.combined_score = p_score * PROBLEM_WEIGHT
                return result

    # Step 2: Cap WTP based on evidence tier
    raw_wtp = problem_scores.get("willingness_to_pay", 5.0)
    capped_wtp, wtp_warning = cap_wtp_score(raw_wtp, wtp_tier)
    if wtp_warning:
        result.wtp_capped = True
        print(f"Warning: {wtp_warning}")
    problem_scores["willingness_to_pay"] = capped_wtp

    # Step 3: Calculate problem score
    p_score, p_breakdown = calculate_problem_score(problem_scores)
    result.problem_score = p_score

    # Step 4: Check market timing elimination
    mt_score = problem_scores.get("market_timing", 5.0)
    if mt_score < MARKET_TIMING_ELIMINATION:
        result.market_timing_eliminated = True
        result.combined_score = p_score * PROBLEM_WEIGHT
        result.verdict = "fail"
        result.reason = f"MARKET TIMING ELIMINATION: {mt_score}/10 < {MARKET_TIMING_ELIMINATION} threshold"
        return result

    # Step 5: Problem score threshold (early elimination)
    if p_score < PASS_THRESHOLD:
        result.combined_score = p_score * PROBLEM_WEIGHT
        result.verdict = "fail"
        result.reason = f"EARLY ELIMINATION: Problem score {p_score:.2f}/10 < {PASS_THRESHOLD}"
        return result

    # Step 6: Solution scoring (only if problem passes)
    if solution_scores:
        s_score = calculate_solution_score(solution_scores)
        result.solution_score = s_score

        # Check competitive advantage floor
        ca_score = solution_scores.get("competitive_advantage", 5.0)
        if ca_score <= COMPETITIVE_ADVANTAGE_FLOOR:
            result.competitive_advantage_floor_hit = True
            result.combined_score = calculate_combined_score(p_score, s_score)
            result.verdict = "fail"
            result.reason = f"COMPETITIVE ADVANTAGE FLOOR: {ca_score}/10 ≤ {COMPETITIVE_ADVANTAGE_FLOOR} (exact product already exists with significant funding)"
            return result

        # Calculate combined score
        combined = calculate_combined_score(p_score, s_score)
        result.combined_score = combined

        # Step 7: Threshold check with smart mediocrity
        if combined >= PASS_THRESHOLD:
            if combined < 6.5:
                # Smart mediocrity check
                sm_verdict, sm_reason = smart_mediocrity_check(
                    combined_score=combined,
                    competitive_advantage=ca_score,
                    wtp_tier=wtp_tier,
                    market_timing=mt_score,
                    strongest_competitor_funding_m=strongest_competitor_funding_m,
                )
                result.smart_mediocrity_result = sm_reason
                result.verdict = sm_verdict
                result.reason = sm_reason
            else:
                result.verdict = "pass"
                result.reason = f"PASS ({combined:.2f}/10)"
        else:
            result.verdict = "fail"
            result.reason = f"FAIL ({combined:.2f}/10 < {PASS_THRESHOLD})"
    else:
        result.combined_score = p_score * PROBLEM_WEIGHT
        result.verdict = "fail"
        result.reason = "No solution scores provided"

    return result


# --- Competitor Analysis ---

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


# --- Customer Segments ---

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


# --- MVP Features ---

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


# --- Scoring Rubric ---

def generate_scoring_rubric() -> Dict:
    """
    Generate the v2.0 scoring rubric for evaluation.

    Returns:
        Dict with scoring criteria and descriptions
    """
    return {
        "pain_severity": {
            "weight": 0.20,
            "scale": "1-10",
            "description": "How severe is the problem objectively for the target customer?",
            "scoring_guide": {
                "1-3": "Nice-to-have, not urgent, low impact on daily operations",
                "4-6": "Important but not critical, workarounds exist",
                "7-8": "Significant pain, actively seeking solutions, measurable cost",
                "9-10": "Critical problem, must solve immediately, existential impact"
            }
        },
        "startup_addressability": {
            "weight": 0.20,
            "scale": "1-10",
            "description": "Given competitors, regulation, and timing — how viable is this for a NEW ENTRANT right now?",
            "scoring_guide": {
                "1-3": "Exact product exists with $50M+ funding, or regulatory prohibition, or market 3+ years away",
                "4-6": "Strong incumbents but identifiable wedge, or moderate regulatory hurdles",
                "7-8": "Clear gap incumbents structurally cannot address, favorable regulatory environment",
                "9-10": "No funded competitor in the space, regulatory tailwind, perfect timing window"
            },
            "note": "This is NOT how bad the problem is — it's how viable the OPPORTUNITY is for a startup entering NOW."
        },
        "market_size": {
            "weight": 0.20,
            "scale": "1-10",
            "description": "How large is the VERIFIED addressable market? Penalize derived SAMs.",
            "scoring_guide": {
                "1-3": "Niche market < $100M, or SAM is speculative/derived",
                "4-6": "Medium market $100M-$1B, SAM methodology partially verified",
                "7-8": "Large market $1B-$10B, SAM from measured data",
                "9-10": "Massive market > $10B, SAM independently verified by multiple sources"
            },
            "note": "Deduct 1 point per layer of derivation in SAM calculation."
        },
        "willingness_to_pay": {
            "weight": 0.20,
            "scale": "1-10",
            "description": "Are customers willing to pay THIS product from a NEW entrant?",
            "scoring_guide": {
                "1-4": "TIER 3: Adjacent category spending only, survey data, analyst projections (CAPPED AT 4)",
                "5-7": "TIER 2: Validated pricing from interviews, competitor revenue for THIS type of product",
                "8-10": "TIER 1: Signed LOIs, existing payments for structurally identical product"
            },
            "tiers": {
                "tier_1": {"max": 10, "evidence": "Direct payments, LOIs, committed budget for identical product"},
                "tier_2": {"max": 7, "evidence": "Interview-validated pricing, competitor revenue proving price point works"},
                "tier_3": {"max": 4, "evidence": "Adjacent category spending, surveys, analyst projections only"}
            }
        },
        "market_timing": {
            "weight": 0.20,
            "scale": "1-10",
            "description": "Is the market ready NOW? Are there paying customers TODAY?",
            "scoring_guide": {
                "1-2": "Market does not exist, pure theoretical, no paying customers",
                "3-4": "Market speculative, no paying customers, 3+ years out → TRIGGERS EARLY ELIMINATION",
                "5-6": "Market emerging, some pilots, 2-3 years to meaningful adoption",
                "7-8": "Market exists, early adopters paying, 12-18 months to mainstream",
                "9-10": "Regulatory forcing function active NOW, buyers urgently allocating budget"
            },
            "threshold": f"< {MARKET_TIMING_ELIMINATION} triggers early elimination"
        },
        "technical_viability": {
            "weight": "solution (25% of 45%)",
            "scale": "1-10",
            "description": "How feasible is the technical implementation?"
        },
        "competitive_advantage": {
            "weight": "solution (25% of 45%)",
            "scale": "1-10",
            "description": "How defensible is the competitive position?",
            "floor": f"≤ {COMPETITIVE_ADVANTAGE_FLOOR} = AUTO-FAIL regardless of other scores",
            "scoring_guide": {
                "1-3": "AUTO-FAIL ZONE: Exact product exists with $50M+ funding, no structural differentiation",
                "4-5": "Weak: Timing advantage only (12-18 month window), features easily replicated",
                "6-7": "Moderate: Specific wedge incumbents structurally can't address for 18-24 months",
                "8-10": "Strong: Genuine moat (data, network effects, regulatory cert) with 2+ years to replicate"
            }
        },
        "resource_requirements": {
            "weight": "solution (25% of 45%)",
            "scale": "1-10",
            "description": "How reasonable are the resource requirements?"
        },
        "time_to_market": {
            "weight": "solution (25% of 45%)",
            "scale": "1-10",
            "description": "How quickly can an MVP be delivered?"
        }
    }


if __name__ == "__main__":
    # Test the v2.0 functions
    print("Testing analysis tools v2.0...")
    print("=" * 50)

    # Test TAM/SAM/SOM calculation
    market = calculate_tam_sam_som(4_200_000_000)
    print(f"TAM: {format_market_size(market.tam)}")
    print(f"SAM: {format_market_size(market.sam)}")
    print(f"SOM: {format_market_size(market.som)}")

    # Test kill switches
    print("\n--- Kill Switch Tests ---")
    ks_comp = check_competitor_kill(True, 100, "Noma Security", "Exact ASPM product")
    print(f"Competitor kill: {ks_comp.triggered} — {ks_comp.reason}")

    ks_reg = check_regulatory_kill(True, regulation_name="FCA PS25/22")
    print(f"Regulatory kill: {ks_reg.triggered} — {ks_reg.reason}")

    ks_time = check_timing_kill(1.5, False, evidence="AI commerce at 1.5%")
    print(f"Timing kill: {ks_time.triggered} — {ks_time.reason}")

    # Test WTP tiers
    print("\n--- WTP Tier Tests ---")
    for tier in WTPTier:
        capped, warning = cap_wtp_score(7.0, tier)
        print(f"  {tier.label}: raw=7.0, capped={capped}, warning={warning}")

    # Test problem score v2.0 (5 criteria)
    print("\n--- Problem Score v2.0 ---")
    scores = {
        "pain_severity": 8,
        "startup_addressability": 4,  # Noma already has the product
        "market_size": 7,
        "willingness_to_pay": 6,
        "market_timing": 7,
    }
    problem_score, breakdown = calculate_problem_score(scores)
    print(f"Problem Score: {problem_score:.2f}")
    print(f"Breakdown: {breakdown}")

    # Test full evaluation with kill switch
    print("\n--- Full Evaluation (Kill Switch Triggered) ---")
    result = run_full_evaluation(
        problem_scores=scores,
        solution_scores={
            "technical_viability": 7,
            "competitive_advantage": 4,
            "resource_requirements": 6,
            "time_to_market": 7,
        },
        kill_switches=[ks_comp],
        wtp_tier=WTPTier.TIER_2,
        strongest_competitor_funding_m=100,
    )
    print(f"Verdict: {result.verdict}")
    print(f"Reason: {result.reason}")

    # Test full evaluation with CA floor
    print("\n--- Full Evaluation (CA Floor Hit) ---")
    result2 = run_full_evaluation(
        problem_scores={
            "pain_severity": 9,
            "startup_addressability": 6,
            "market_size": 8,
            "willingness_to_pay": 7,
            "market_timing": 8,
        },
        solution_scores={
            "technical_viability": 7,
            "competitive_advantage": 3,  # Floor hit
            "resource_requirements": 6,
            "time_to_market": 7,
        },
        wtp_tier=WTPTier.TIER_2,
    )
    print(f"Verdict: {result2.verdict}")
    print(f"Reason: {result2.reason}")

    # Test smart mediocrity
    print("\n--- Smart Mediocrity Check ---")
    sm_verdict, sm_reason = smart_mediocrity_check(
        combined_score=6.2,
        competitive_advantage=5,
        wtp_tier=WTPTier.TIER_3,
        market_timing=5,
        strongest_competitor_funding_m=80,
    )
    print(f"Smart mediocrity: {sm_verdict} — {sm_reason}")

    print("\n--- Scoring Rubric v2.0 ---")
    rubric = generate_scoring_rubric()
    for key, val in rubric.items():
        print(f"  {key}: {val.get('description', '')}")
