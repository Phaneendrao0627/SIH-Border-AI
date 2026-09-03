"""Unit tests for score aggregation, weight renormalization, and risk tier guardrails."""

import pytest

from tampering_detection.config import DetectionConfig
from tampering_detection.schemas import EvidenceItem, RiskLevel, SeverityLevel
from tampering_detection.scoring.score_aggregator import aggregate_scores


def test_weight_renormalization():
    """Test 18: Renormalization correctly computes weighted sum when optional detectors are skipped."""
    config = DetectionConfig(
        weight_metadata=0.10,
        weight_ela=0.30,
        weight_photo=0.25,
        weight_text=0.20,
        weight_stamp=0.15,
    )

    # Scenario: photo and stamp regions are skipped (None)
    # Active weights: metadata (0.10), ela (0.30), text (0.20) -> sum = 0.60
    # Normalized weights: meta = 1/6, ela = 3/6 (0.5), text = 2/6 (0.3333)
    detector_scores = {
        "metadata": 0.0,
        "ela": 60.0,
        "photo": None,
        "text": 30.0,
        "stamp": None,
    }

    # Expected score: (0 * 1/6) + (60 * 3/6) + (30 * 2/6) = 0 + 30 + 10 = 40
    score, risk = aggregate_scores(detector_scores, [], config)
    assert score == 40
    assert risk == RiskLevel.MEDIUM


def test_score_always_remains_between_0_and_100():
    """Test 19: Tampering score is guaranteed to remain strictly bounded [0, 100]."""
    config = DetectionConfig()

    # Extreme over-range input
    over_scores = {
        "metadata": 999.0,
        "ela": 500.0,
        "photo": 150.0,
        "text": 200.0,
        "stamp": 300.0,
    }
    score_max, risk_max = aggregate_scores(over_scores, [], config)
    assert 0 <= score_max <= 100

    # Negative input
    under_scores = {
        "metadata": -50.0,
        "ela": -10.0,
        "photo": -20.0,
        "text": -5.0,
        "stamp": -100.0,
    }
    score_min, risk_min = aggregate_scores(under_scores, [], config)
    assert 0 <= score_min <= 100
    assert score_min == 0
    assert risk_min == RiskLevel.LOW


def test_metadata_only_cannot_produce_high_or_critical():
    """Verify safety guardrail: elevated metadata alone cannot trigger HIGH or CRITICAL risk."""
    config = DetectionConfig()

    detector_scores = {
        "metadata": 50.0,
        "ela": 5.0,
        "photo": 0.0,
        "text": 0.0,
        "stamp": 0.0,
    }

    score, risk = aggregate_scores(detector_scores, [], config)
    assert score < 60
    assert risk in (RiskLevel.LOW, RiskLevel.MEDIUM)


def test_critical_risk_requires_corroboration():
    """Verify safety guardrail: isolated single high signal without corroboration is capped at HIGH (79)."""
    config = DetectionConfig()

    # One detector reports 95, but all others are zero and evidence is singular
    detector_scores = {
        "metadata": 0.0,
        "ela": 95.0,
        "photo": 0.0,
        "text": 0.0,
        "stamp": 0.0,
    }

    score, risk = aggregate_scores(detector_scores, [], config)
    assert score < 80
    assert risk != RiskLevel.CRITICAL
