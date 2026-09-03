"""Unit tests for text manipulation, stroke consistency, and rectangular patch artifacts."""

import cv2
import numpy as np
import pytest

from tampering_detection.config import DetectionConfig
from tampering_detection.detectors.text_detector import TextDetector
from tampering_detection.io.image_loader import load_image
from tampering_detection.schemas import DocumentRegions, RegionCoordinate


def test_text_detector_skipped_gracefully():
    """Verify text detector skips gracefully when no text regions provided."""
    arr = np.full((300, 400, 3), 200, dtype=np.uint8)
    loaded = load_image(arr)

    detector = TextDetector()
    config = DetectionConfig()
    result, evidence, warnings = detector.run(loaded, DocumentRegions(), config)

    assert result.enabled is False
    assert result.score is None
    assert result.regions_analyzed == 0


def test_text_manipulation_pasted_block(clean_synthetic_document):
    """Test 6: Pasted text block with erased patch triggers rectangular_paste_boundary."""
    doc, regions = clean_synthetic_document
    tampered = doc.copy()

    # Paste pure flat white box over text region
    cv2.rectangle(tampered, (240, 160), (390, 195), (255, 255, 255), -1)
    cv2.putText(tampered, "99999999", (245, 185), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 0), 3)

    loaded = load_image(tampered)
    detector = TextDetector()
    config = DetectionConfig()

    result, evidence, warnings = detector.run(loaded, regions, config)

    assert result.enabled is True
    assert "rectangular_paste_boundary" in result.signals
    assert result.score is not None and result.score > 25.0


def test_single_text_region_does_not_claim_cross_consistency(clean_synthetic_document):
    """Verify single text region reports limited context rather than false cross-field inconsistency."""
    doc, _ = clean_synthetic_document
    single_region = DocumentRegions(
        text=[RegionCoordinate(name="isolated_text", x=240, y=100, width=180, height=35)]
    )

    loaded = load_image(doc)
    detector = TextDetector()
    config = DetectionConfig()

    result, evidence, warnings = detector.run(loaded, single_region, config)

    assert result.enabled is True
    assert result.regions_analyzed == 1
    assert "pixel_density_inconsistency" not in result.signals
    assert any("INSUFFICIENT_EVIDENCE" in w for w in warnings)
