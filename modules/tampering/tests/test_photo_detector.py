"""Unit tests for photo replacement, boundary discontinuity, and noise mismatch."""

import numpy as np
import pytest

from tampering_detection.config import DetectionConfig
from tampering_detection.detectors.photo_detector import PhotoDetector
from tampering_detection.io.image_loader import load_image
from tampering_detection.schemas import DocumentRegions, RegionCoordinate


def test_photo_detector_skipped_gracefully():
    """Verify photo detector skips gracefully when no photo regions are provided."""
    arr = np.full((300, 400, 3), 200, dtype=np.uint8)
    loaded = load_image(arr)

    detector = PhotoDetector()
    config = DetectionConfig()
    result, evidence, warnings = detector.run(loaded, DocumentRegions(), config)

    assert result.enabled is False
    assert result.score is None
    assert result.regions_analyzed == 0
    assert result.reason is not None


def test_photo_pasted_rectangle(clean_synthetic_document):
    """Test 4: Abrupt rectangular paste boundary triggers boundary_discontinuity."""
    doc, regions = clean_synthetic_document
    tampered = doc.copy()

    # Create sharp contrasting border around photo
    px, py, pw, ph = 50, 80, 160, 200
    # Fill photo with significantly darker background
    tampered[py : py + ph, px : px + pw] = 40

    loaded = load_image(tampered)
    detector = PhotoDetector()
    config = DetectionConfig()

    result, evidence, warnings = detector.run(loaded, regions, config)

    assert result.enabled is True
    assert result.photo_replacement_suspected is True
    assert "boundary_discontinuity" in result.signals
    assert result.score is not None and result.score >= 25.0


def test_photo_noise_mismatch(clean_synthetic_document):
    """Test 5: High-frequency noise disparity inside photo region triggers noise_pattern_mismatch."""
    doc, regions = clean_synthetic_document
    tampered = doc.copy()

    px, py, pw, ph = 50, 80, 160, 200
    # Inject heavy Gaussian noise into photo region
    np.random.seed(99)
    noise = np.random.normal(0, 30, (ph, pw, 3)).astype(np.int16)
    noisy_photo = np.clip(tampered[py : py + ph, px : px + pw].astype(np.int16) + noise, 0, 255).astype(np.uint8)
    tampered[py : py + ph, px : px + pw] = noisy_photo

    loaded = load_image(tampered)
    detector = PhotoDetector()
    config = DetectionConfig()

    result, evidence, warnings = detector.run(loaded, regions, config)

    assert result.enabled is True
    assert "noise_pattern_mismatch" in result.signals
    # Verify cautious evidence language
    for ev in evidence:
        assert "definitely forged" not in ev.description.lower()
        assert "arrest" not in ev.description.lower()
