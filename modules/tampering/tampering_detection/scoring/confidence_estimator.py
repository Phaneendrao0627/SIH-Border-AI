"""Holistic confidence estimation based on image quality, detector coverage, and signal agreement."""

from typing import Any, Dict, List, Optional

from tampering_detection.config import DetectionConfig
from tampering_detection.schemas import EvidenceItem, ImageQualityMetrics, SeverityLevel


def estimate_confidence(
    quality: ImageQualityMetrics,
    detectors_run: List[str],
    detectors_skipped: List[str],
    evidence: List[EvidenceItem],
    detector_scores: Dict[str, Optional[float]],
    config: DetectionConfig,
    warnings: Optional[List[str]] = None,
) -> float:
    """Calculate overall reliability and confidence score for the tampering analysis.

    Factors:
    - Image resolution: low resolution attenuates confidence.
    - Image sharpness: severe blur reduces confidence.
    - Photometric anomalies: over/underexposure penalizes confidence.
    - Detector coverage: running more detectors across provided regions increases confidence.
    - Detector agreement / corroboration: multiple detectors agreeing increases confidence.
    - Warnings and exceptions: degrade confidence.

    Returns:
        Confidence float bounded between 0.10 and 0.98.
    """
    base_confidence = 0.80

    # 1. Quality impacts
    if quality.low_resolution:
        base_confidence -= 0.18

    if quality.blur_score < config.blur_threshold:
        blur_deficit = max(0.0, 1.0 - (quality.blur_score / max(config.blur_threshold, 1.0)))
        base_confidence -= min(0.25, 0.10 + 0.15 * blur_deficit)

    if quality.is_overexposed or quality.is_underexposed:
        base_confidence -= 0.08

    if quality.contrast_score < config.min_contrast_std:
        base_confidence -= 0.08

    # 2. Detector coverage
    # Out of 5 total detectors (metadata, ela, photo, text, stamp)
    total_possible = 5
    coverage_ratio = len(detectors_run) / float(total_possible)
    if coverage_ratio >= 0.8:
        base_confidence += 0.08
    elif coverage_ratio <= 0.4:
        base_confidence -= 0.12

    # 3. Inter-detector corroboration
    # Count how many detectors produced elevated scores (>= 40)
    elevated_detectors = [
        name for name, score in detector_scores.items()
        if score is not None and score >= 40.0
    ]

    if len(elevated_detectors) >= 2:
        # Strong multi-detector agreement
        base_confidence += 0.10
    elif len(elevated_detectors) == 1 and len(detectors_run) >= 3:
        # Isolated signal among clean signals slightly moderates confidence
        base_confidence += 0.02

    # 4. Warnings penalty
    if warnings:
        for w in warnings:
            if "INTERNAL_ERROR" in w or "INTERNAL_DETECTOR_ERROR" in w:
                base_confidence -= 0.15
            elif "INVALID_REGION" in w or "REGION_TOO_SMALL" in w:
                base_confidence -= 0.05

    # Clamp confidence between 0.10 and 0.98
    final_conf = max(0.10, min(0.98, base_confidence))
    return round(final_conf, 2)
