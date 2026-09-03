"""Unit tests for region coordinate validation, boundary clamping, and size filters."""

import pytest

from tampering_detection.preprocessing.region_validation import validate_and_clamp_regions
from tampering_detection.schemas import DocumentRegions


def test_missing_region_coordinates():
    """Test 15: Passing None or empty regions dictionary returns empty DocumentRegions safely."""
    regions_none, warnings_none = validate_and_clamp_regions(None, 800, 600)
    assert isinstance(regions_none, DocumentRegions)
    assert len(regions_none.photo) == 0
    assert len(regions_none.text) == 0
    assert len(regions_none.stamp) == 0
    assert len(warnings_none) == 0

    regions_empty, warnings_empty = validate_and_clamp_regions({}, 800, 600)
    assert isinstance(regions_empty, DocumentRegions)


def test_invalid_region_coordinates():
    """Test 14: Out-of-bounds coordinates are clamped and invalid entries produce warnings."""
    raw_regions = {
        "photo": [
            # Partially outside right boundary -> clamped
            {"name": "photo_clamped", "x": 750, "y": 100, "width": 150, "height": 200},
            # Completely outside image -> skipped
            {"name": "photo_outside", "x": 900, "y": 900, "width": 100, "height": 100},
            # Negative coordinates -> clamped
            {"name": "photo_negative", "x": -50, "y": -20, "width": 150, "height": 150},
        ]
    }

    validated, warnings = validate_and_clamp_regions(raw_regions, image_width=800, image_height=600)

    # photo_outside should be skipped
    names = [p.name for p in validated.photo]
    assert "photo_outside" not in names
    assert "photo_clamped" in names

    # Verify clamping
    clamped = next(p for p in validated.photo if p.name == "photo_clamped")
    assert clamped.x + clamped.width <= 800

    # Warnings should record clamping and skipping
    assert any("clamped" in w for w in warnings)
    assert any("INVALID_REGION" in w for w in warnings)


def test_tiny_region():
    """Test 16: Regions smaller than category minimum dimensions produce REGION_TOO_SMALL warning."""
    raw_regions = {
        "text": [
            {"name": "tiny_text", "x": 100, "y": 100, "width": 5, "height": 3}
        ]
    }

    validated, warnings = validate_and_clamp_regions(raw_regions, image_width=800, image_height=600)

    # Sub-threshold region should be excluded from active text regions
    assert len(validated.text) == 0
    assert any("REGION_TOO_SMALL" in w for w in warnings)
