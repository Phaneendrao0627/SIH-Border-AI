"""Weighted tampering score aggregation and risk tier classification with dynamic renormalization."""

from typing import Dict, List, Optional, Tuple

from tampering_detection.config import DetectionConfig
from tampering_detection.logging_config import get_logger
from tampering_detection.schemas import EvidenceItem, RiskLevel, SeverityLevel

logger = get_logger("scoring.score_aggregator")


def aggregate_scores(
    detector_scores: Dict[str, Optional[float]],
    evidence: List[EvidenceItem],
    config: DetectionConfig,
) -> Tuple[int, RiskLevel]:
    """Aggregate individual detector outputs into a normalized document tampering score (0-100) and risk level.

    Features:
    - Dynamic weight renormalization when detectors are skipped.
    - Strict boundary guarantees [0, 100].
    - Safety guardrails: metadata-only alerts cannot trigger HIGH or CRITICAL risk.
    - Stringent criteria for CRITICAL risk (requires multiple corroborating forensic signals).

    Args:
        detector_scores: Dict mapping detector key ("metadata", "ela", "photo", "text", "stamp")
                         to their respective score (0-100) or None if skipped.
        evidence: List of generated forensic evidence items.
        config: Central configuration containing baseline weights and thresholds.

    Returns:
        Tuple of (tampering_score: int [0-100], risk_level: RiskLevel).
    """
    base_weights: Dict[str, float] = {
        "metadata": config.weight_metadata,
        "ela": config.weight_ela,
        "photo": config.weight_photo,
        "text": config.weight_text,
        "stamp": config.weight_stamp,
    }

    # 1. Determine active detectors and sum their baseline weights
    active_detectors = {
        key: score for key, score in detector_scores.items()
        if score is not None and key in base_weights
    }

    if not active_detectors:
        logger.warning("No active detectors available for aggregation; returning 0 LOW.")
        return 0, RiskLevel.LOW

    total_active_weight = sum(base_weights[key] for key in active_detectors.keys())

    # Avoid divide by zero
    if total_active_weight <= 0.0:
        total_active_weight = 1.0

    # 2. Compute renormalized weighted score
    raw_score = 0.0
    for key, score in active_detectors.items():
        renormalized_weight = base_weights[key] / total_active_weight
        # Enforce detector score is clamped [0, 100]
        clamped_detector_score = max(0.0, min(100.0, float(score)))
        raw_score += renormalized_weight * clamped_detector_score

    # 3. Apply Safety Guardrails

    # Guardrail A: Metadata-only restriction
    # If only metadata is elevated (> 10.0) while all other active visual/statistical detectors are low (<= 15.0)
    visual_elevated = any(
        (s is not None and s > 15.0)
        for k, s in active_detectors.items()
        if k != "metadata"
    )
    metadata_elevated = (active_detectors.get("metadata") or 0.0) > 20.0

    if metadata_elevated and not visual_elevated:
        # Metadata alone cannot exceed 50 points or produce HIGH/CRITICAL risk
        raw_score = min(raw_score, 49.0)

    # Guardrail B: CRITICAL risk stringent requirements
    # Critical (>= 80) requires multiple independent high-severity indicators
    high_evidence_count = sum(
        1 for e in evidence
        if e.severity in (SeverityLevel.HIGH, SeverityLevel.CRITICAL)
    )
    strongly_elevated_detectors = sum(
        1 for s in active_detectors.values()
        if s is not None and s >= 60.0
    )

    meets_critical_criteria = (
        (strongly_elevated_detectors >= 2)
        or (strongly_elevated_detectors >= 1 and high_evidence_count >= 2)
    )

    if raw_score >= config.threshold_high and not meets_critical_criteria:
        # Single isolated high signal capped at HIGH risk boundary (79)
        raw_score = min(raw_score, float(config.threshold_high - 1))

    # Guardrail C: Bound final score between 0 and 100
    final_score = int(round(max(0.0, min(100.0, raw_score))))

    # 4. Map to Risk Tier
    if final_score < config.threshold_low:
        risk_level = RiskLevel.LOW
    elif final_score < config.threshold_medium:
        risk_level = RiskLevel.MEDIUM
    elif final_score < config.threshold_high:
        risk_level = RiskLevel.HIGH
    else:
        risk_level = RiskLevel.CRITICAL

    return final_score, risk_level
