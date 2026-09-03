"""Scoring and confidence estimation modules."""

from tampering_detection.scoring.confidence_estimator import estimate_confidence
from tampering_detection.scoring.score_aggregator import aggregate_scores

__all__ = ["aggregate_scores", "estimate_confidence"]
