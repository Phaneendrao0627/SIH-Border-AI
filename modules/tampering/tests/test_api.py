"""End-to-end integration tests for the public analyze_document API."""

import json
import pytest

from tampering_detection.api import analyze_document
from tampering_detection.config import DetectionConfig
from tampering_detection.schemas import RiskLevel, TamperingDetectionResult


def test_clean_synthetic_document(clean_synthetic_document):
    """Test 1: Clean synthetic document receives low tampering score and LOW risk."""
    doc_array, regions = clean_synthetic_document
    config = DetectionConfig(privacy_mode=True)

    result = analyze_document(
        image_source=doc_array,
        document_id="TEST-CLEAN-001",
        document_type="passport",
        regions=regions,
        options=config,
    )

    assert isinstance(result, TamperingDetectionResult)
    assert result.status == "completed"
    assert result.tampering_score < 35
    assert result.risk_level in (RiskLevel.LOW, RiskLevel.MEDIUM)
    assert result.confidence > 0.60
    assert "photo_replacement_suspected" not in result.flags


def test_tampered_photo_detection(tampered_photo_document):
    """Test 4 & 5: Document with spliced/noisy photo raises photo flags and elevated score."""
    tampered_doc, regions = tampered_photo_document
    config = DetectionConfig(privacy_mode=True)

    result = analyze_document(
        image_source=tampered_doc,
        document_id="TEST-PHOTO-FORGERY",
        document_type="id_card",
        regions=regions,
        options=config,
    )

    assert result.tampering_analysis.photo_analysis.enabled is True
    assert result.tampering_analysis.photo_analysis.score is not None
    assert result.tampering_analysis.photo_analysis.score > 30.0
    assert len(result.evidence) > 0


def test_tampered_text_detection(tampered_text_document):
    """Test 6: Document with altered text block raises text manipulation flags."""
    tampered_doc, regions = tampered_text_document
    config = DetectionConfig(privacy_mode=True)

    result = analyze_document(
        image_source=tampered_doc,
        document_id="TEST-TEXT-TAMPER",
        document_type="visa",
        regions=regions,
        options=config,
    )

    assert result.tampering_analysis.text_analysis.enabled is True
    assert result.tampering_analysis.text_analysis.score is not None
    assert result.tampering_analysis.text_analysis.score >= 25.0


def test_json_serialization_works(clean_synthetic_document):
    """Test 20: TamperingDetectionResult cleanly serializes to valid JSON."""
    doc_array, regions = clean_synthetic_document
    config = DetectionConfig(privacy_mode=True)

    result = analyze_document(
        image_source=doc_array,
        document_id="TEST-JSON-SERIALIZE",
        regions=regions,
        options=config,
    )

    dumped = result.model_dump()
    assert isinstance(dumped, dict)
    assert dumped["schema_version"] == "1.0"
    assert "tampering_score" in dumped
    assert "tampering_analysis" in dumped

    # Must serialize to string without TypeError
    json_str = json.dumps(dumped)
    assert len(json_str) > 0
