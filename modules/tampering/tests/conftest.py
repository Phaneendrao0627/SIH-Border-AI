"""Pytest fixtures and synthetic document generators for forensic testing."""

import io
from pathlib import Path
from typing import Dict, Tuple

import cv2
import numpy as np
from PIL import Image, PngImagePlugin
import pytest

from tampering_detection.config import DetectionConfig
from tampering_detection.schemas import DocumentRegions, RegionCoordinate


@pytest.fixture
def sample_config():
    """Default configuration fixture for testing."""
    return DetectionConfig(privacy_mode=True)


@pytest.fixture
def sample_regions():
    """Standard document regions fixture."""
    return DocumentRegions(
        photo=[RegionCoordinate(name="document_photo", x=50, y=80, width=160, height=200)],
        text=[
            RegionCoordinate(name="full_name", x=240, y=100, width=180, height=35),
            RegionCoordinate(name="doc_number", x=240, y=160, width=150, height=35),
        ],
        stamp=[RegionCoordinate(name="entry_stamp", x=220, y=240, width=160, height=80)],
    )


@pytest.fixture
def clean_synthetic_document() -> Tuple[np.ndarray, DocumentRegions]:
    """Generate an authentic-looking clean synthetic document array."""
    w, h = 600, 400
    doc = np.full((h, w, 3), 245, dtype=np.uint8)
    np.random.seed(42)
    noise = np.random.normal(0, 2, (h, w, 3)).astype(np.int16)
    doc = np.clip(doc.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    # Document Header
    cv2.putText(doc, "GENUINE SAMPLE DOCUMENT", (150, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (50, 50, 50), 2)

    # Photo region (x=50, y=80, w=160, h=200)
    photo = np.full((200, 160, 3), 225, dtype=np.uint8)
    p_noise = np.random.normal(0, 2, (200, 160, 3)).astype(np.int16)
    photo = np.clip(photo.astype(np.int16) + p_noise, 0, 255).astype(np.uint8)
    cv2.circle(photo, (80, 80), 35, (130, 130, 130), -1)
    doc[80:280, 50:210] = photo

    # Text fields
    cv2.putText(doc, "NAME: JOHN DOE", (245, 125), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (40, 40, 40), 1)
    cv2.putText(doc, "ID: 12345678", (245, 185), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (40, 40, 40), 1)

    # Stamp
    cv2.rectangle(doc, (230, 250), (370, 310), (0, 0, 180), 2)
    cv2.putText(doc, "VERIFIED", (255, 285), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 180), 1)

    regions = DocumentRegions(
        photo=[RegionCoordinate(name="document_photo", x=50, y=80, width=160, height=200)],
        text=[
            RegionCoordinate(name="full_name", x=240, y=100, width=180, height=35),
            RegionCoordinate(name="doc_number", x=240, y=160, width=150, height=35),
        ],
        stamp=[RegionCoordinate(name="entry_stamp", x=220, y=240, width=160, height=80)],
    )

    return doc, regions


@pytest.fixture
def tampered_photo_document(clean_synthetic_document) -> Tuple[np.ndarray, DocumentRegions]:
    """Generate document with spliced high-noise photo."""
    doc, regions = clean_synthetic_document
    tampered = doc.copy()

    # Splice mismatched photo with high noise and dark tone
    high_noise_photo = np.full((200, 160, 3), 110, dtype=np.uint8)
    h_noise = np.random.normal(0, 25, (200, 160, 3)).astype(np.int16)
    high_noise_photo = np.clip(high_noise_photo.astype(np.int16) + h_noise, 0, 255).astype(np.uint8)
    tampered[80:280, 50:210] = high_noise_photo

    return tampered, regions


@pytest.fixture
def tampered_text_document(clean_synthetic_document) -> Tuple[np.ndarray, DocumentRegions]:
    """Generate document with white box erased and mismatched text."""
    doc, regions = clean_synthetic_document
    tampered = doc.copy()

    # Text region 2 (doc_number at x=240, y=160, w=150, h=35)
    # Erase with flat white box and write darker, thicker font
    cv2.rectangle(tampered, (240, 160), (390, 195), (255, 255, 255), -1)
    cv2.putText(tampered, "ID: 99999999", (245, 185), cv2.FONT_HERSHEY_SIMPLEX, 0.70, (0, 0, 0), 3)

    return tampered, regions


@pytest.fixture
def duplicate_stamp_document(clean_synthetic_document) -> Tuple[np.ndarray, DocumentRegions]:
    """Generate document with duplicated clone stamp."""
    doc, regions = clean_synthetic_document
    tampered = doc.copy()

    # Clone stamp 1 and paste as stamp 2
    stamp_crop = tampered[240:320, 220:380].copy()
    tampered[240:320, 400:560] = stamp_crop

    dup_regions = DocumentRegions(
        photo=regions.photo,
        text=regions.text,
        stamp=[
            RegionCoordinate(name="stamp_original", x=220, y=240, width=160, height=80),
            RegionCoordinate(name="stamp_duplicate", x=400, y=240, width=160, height=80),
        ],
    )
    return tampered, dup_regions
