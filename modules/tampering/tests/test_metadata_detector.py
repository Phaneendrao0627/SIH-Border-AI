"""Unit tests for metadata extraction and EXIF editing software detection."""

import io
from PIL import Image, PngImagePlugin
import pytest

from tampering_detection.config import DetectionConfig
from tampering_detection.detectors.metadata_detector import MetadataDetector
from tampering_detection.io.image_loader import load_image
from tampering_detection.schemas import DocumentRegions


def test_metadata_editing_software():
    """Test 2: Editing software tags in metadata are detected and flagged."""
    # Create PNG image with Software header indicating Adobe Photoshop
    img = Image.new("RGB", (400, 300), color=(240, 240, 240))
    info = PngImagePlugin.PngInfo()
    info.add_text("Software", "Adobe Photoshop 2024 (Windows)")

    buf = io.BytesIO()
    img.save(buf, format="PNG", pnginfo=info)
    raw_bytes = buf.getvalue()

    loaded = load_image(raw_bytes)
    detector = MetadataDetector()
    config = DetectionConfig()

    result, evidence, warnings = detector.run(loaded, DocumentRegions(), config)

    assert result.available is True
    assert "editing_software_detected" in result.flags
    assert "suspicious_software_string" in result.flags
    assert result.software is not None
    assert "photoshop" in result.software.lower()
    # Metadata score must be strictly capped at 50.0
    assert result.score <= 50.0
    assert result.score > 0.0
    assert len(evidence) > 0


def test_metadata_stripped():
    """Test 3: Image with no EXIF metadata flags metadata_unavailable gracefully."""
    # Plain JPEG created without EXIF
    img = Image.new("RGB", (400, 300), color=(230, 230, 230))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    raw_bytes = buf.getvalue()

    loaded = load_image(raw_bytes)
    detector = MetadataDetector()
    config = DetectionConfig()

    result, evidence, warnings = detector.run(loaded, DocumentRegions(), config)

    assert "metadata_unavailable" in result.flags or "metadata_stripped_or_minimal" in result.flags
    # Missing metadata must not cause a high tampering score
    assert result.score <= 15.0


def test_metadata_score_cap():
    """Verify that even with multiple suspicious flags, metadata score never exceeds 50.0."""
    detector = MetadataDetector()
    config = DetectionConfig()

    img = Image.new("RGB", (400, 300), color=(200, 200, 200))
    info = PngImagePlugin.PngInfo()
    info.add_text("Software", "GIMP 2.10.32")
    info.add_text("Comment", "Edited in Canva")

    buf = io.BytesIO()
    img.save(buf, format="PNG", pnginfo=info)

    loaded = load_image(buf.getvalue())
    result, _, _ = detector.run(loaded, DocumentRegions(), config)

    assert result.score <= 50.0
