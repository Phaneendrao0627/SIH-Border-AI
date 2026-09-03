"""Unit tests for Error Level Analysis (ELA) detector and statistics."""

import numpy as np
from PIL import Image
import pytest

from tampering_detection.config import DetectionConfig
from tampering_detection.detectors.ela_detector import ElaDetector
from tampering_detection.io.image_loader import load_image
from tampering_detection.schemas import DocumentRegions, RegionCoordinate


def test_ela_clean_image():
    """Verify ELA on a uniformly compressed clean image produces low variance and baseline score."""
    # Create clean image and save at quality 90
    arr = np.full((300, 400, 3), 200, dtype=np.uint8)
    loaded = load_image(arr)

    detector = ElaDetector()
    config = DetectionConfig(ela_jpeg_quality=90)

    result, evidence, warnings, ctx = detector.run(loaded, DocumentRegions(), config)

    assert result.enabled is True
    assert result.score < 40.0
    assert result.global_mean >= 0.0
    assert result.global_p95 >= result.global_mean
    assert "ela_gray" in ctx


def test_ela_spliced_region_anomaly():
    """Verify ELA flags elevated difference when an uncompressed patch is spliced onto a recompressed image."""
    import io
    # 1. Base compressed at quality 60
    base = Image.new("RGB", (400, 300), color=(220, 220, 220))
    buf = io.BytesIO()
    base.save(buf, format="JPEG", quality=60)
    buf.seek(0)
    recompressed_base = Image.open(buf).convert("RGB")
    arr = np.array(recompressed_base)

    # 2. Splice a high-frequency noisy patch that was never compressed at 60
    patch = np.random.randint(50, 200, size=(100, 100, 3), dtype=np.uint8)
    arr[50:150, 50:150] = patch

    loaded = load_image(arr)
    detector = ElaDetector()
    config = DetectionConfig(ela_jpeg_quality=90)
    regions = DocumentRegions(
        photo=[RegionCoordinate(name="spliced_photo", x=50, y=50, width=100, height=100)]
    )

    result, evidence, warnings, ctx = detector.run(loaded, regions, config)

    assert result.score > 20.0
    assert "spliced_photo" in ctx.get("regional_ela_stats", {})
    # Ensure limitations disclaimer is provided
    assert len(result.limitations) > 0
