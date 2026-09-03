"""Unit tests for stamp forgery, texture modeling, and duplicated stamp detection."""

import cv2
import numpy as np
import pytest

from tampering_detection.config import DetectionConfig
from tampering_detection.detectors.stamp_detector import StampDetector
from tampering_detection.io.image_loader import load_image
from tampering_detection.schemas import DocumentRegions, RegionCoordinate


def test_stamp_detector_skipped_gracefully():
    """Verify stamp detector skips gracefully when no stamp regions provided."""
    arr = np.full((300, 400, 3), 200, dtype=np.uint8)
    loaded = load_image(arr)

    detector = StampDetector()
    config = DetectionConfig()
    result, evidence, warnings = detector.run(loaded, DocumentRegions(), config)

    assert result.enabled is False
    assert result.score is None
    assert result.regions_analyzed == 0


def test_stamp_duplicate_pattern(duplicate_stamp_document):
    """Test 7: Cloned stamp pattern triggers duplicate detection."""
    tampered_doc, dup_regions = duplicate_stamp_document
    loaded = load_image(tampered_doc)

    detector = StampDetector()
    config = DetectionConfig()

    result, evidence, warnings = detector.run(loaded, dup_regions, config)

    assert result.enabled is True
    assert (
        "identical_stamp_duplicate" in result.signals
        or "possible_duplicated_pattern" in result.signals
    )
    assert result.duplicate_pattern_score is not None
    assert result.duplicate_pattern_score > 30.0


def test_stamp_flat_background_anomaly():
    """Verify digital stamp pasted onto unnatural pure flat background triggers flat_pasted_background."""
    doc = np.full((400, 600, 3), 230, dtype=np.uint8)

    # Stamp region with perfectly flat 0-variance background
    sx, sy, sw, sh = 200, 200, 160, 80
    doc[sy : sy + sh, sx : sx + sw] = 255  # Pure flat white box
    # Draw stamp graphics
    cv2.circle(doc, (sx + sw // 2, sy + sh // 2), 30, (0, 0, 180), 2)
    cv2.putText(doc, "ENTRY", (sx + 45, sy + 45), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 180), 2)

    loaded = load_image(doc)
    detector = StampDetector()
    config = DetectionConfig(stamp_flat_background_threshold=15.0)

    regions = DocumentRegions(
        stamp=[RegionCoordinate(name="pasted_stamp", x=sx, y=sy, width=sw, height=sh)]
    )

    result, evidence, warnings = detector.run(loaded, regions, config)

    assert result.enabled is True
    assert "flat_pasted_background" in result.signals
