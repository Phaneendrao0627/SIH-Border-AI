"""Unit tests for edge cases: blur, low resolution, privacy mode, and detector isolation."""

from pathlib import Path
from unittest.mock import patch

import cv2
import numpy as np
import pytest

from tampering_detection.api import analyze_document
from tampering_detection.config import DetectionConfig
from tampering_detection.detectors.photo_detector import PhotoDetector
from tampering_detection.schemas import DocumentRegions, RegionCoordinate


def test_blurry_image(clean_synthetic_document):
    """Test 12: Heavily blurred image reduces confidence rather than inflating tampering score."""
    doc, regions = clean_synthetic_document
    # Apply severe Gaussian blur
    blurry_doc = cv2.GaussianBlur(doc, (35, 35), 0)

    config = DetectionConfig(privacy_mode=True)
    result = analyze_document(
        image_source=blurry_doc,
        document_id="TEST-BLUR-01",
        regions=regions,
        options=config,
    )

    assert result.quality.blur_score < config.blur_threshold
    # Confidence should be noticeably penalized due to blur
    assert result.confidence < 0.70
    # Blur should not turn clean document into CRITICAL risk
    assert result.tampering_score < 50


def test_very_low_resolution_image():
    """Test 13: Very low resolution image flags low_resolution and reduces confidence."""
    # 100x80 thumbnail image
    small_img = np.full((80, 100, 3), 200, dtype=np.uint8)
    config = DetectionConfig(privacy_mode=True)

    result = analyze_document(
        image_source=small_img,
        document_id="TEST-LOWRES-01",
        options=config,
    )

    assert result.quality.low_resolution is True
    assert result.confidence < 0.70


def test_artifacts_disabled(tmp_path, clean_synthetic_document):
    """Test 21: When save_artifacts=False, no visualization files are written to disk."""
    doc, regions = clean_synthetic_document
    art_dir = tmp_path / "test_artifacts_disabled"

    config = DetectionConfig(
        save_artifacts=False,
        artifacts_dir=str(art_dir),
    )

    result = analyze_document(
        image_source=doc,
        document_id="TEST-NO-ART",
        regions=regions,
        options=config,
    )

    assert result.artifacts.ela_map is None
    assert result.artifacts.ela_overlay is None
    assert len(result.artifacts.region_visualizations) == 0
    assert not art_dir.exists()


def test_privacy_mode_enabled(tmp_path, clean_synthetic_document):
    """Test 22: privacy_mode=True strictly blocks artifact saving even if save_artifacts=True."""
    doc, regions = clean_synthetic_document
    art_dir = tmp_path / "test_privacy_artifacts"

    config = DetectionConfig(
        privacy_mode=True,
        save_artifacts=True,  # Overridden by privacy_mode
        artifacts_dir=str(art_dir),
    )

    result = analyze_document(
        image_source=doc,
        document_id="TEST-PRIVACY",
        regions=regions,
        options=config,
    )

    assert result.artifacts.ela_map is None
    assert result.artifacts.ela_overlay is None
    assert len(result.artifacts.region_visualizations) == 0
    assert not art_dir.exists()


def test_detector_failure_fallback(clean_synthetic_document):
    """Test 17: Detector throwing unhandled exception is gracefully trapped without aborting pipeline."""
    doc, regions = clean_synthetic_document
    config = DetectionConfig(privacy_mode=True)

    # Mock PhotoDetector.run to simulate an unhandled internal detector crash
    with patch.object(PhotoDetector, "run", side_effect=RuntimeError("Simulated CUDA/C++ fault")):
        result = analyze_document(
            image_source=doc,
            document_id="TEST-FALLBACK",
            regions=regions,
            options=config,
        )

    # Pipeline completes successfully despite one detector failing
    assert result.status == "completed"
    assert "photo" in result.processing.detectors_skipped
    assert any("INTERNAL_DETECTOR_ERROR" in w for w in result.warnings)
