"""Forensic tampering detectors package."""

from tampering_detection.detectors.base import BaseDetector
from tampering_detection.detectors.metadata_detector import MetadataDetector
from tampering_detection.detectors.ela_detector import ElaDetector
from tampering_detection.detectors.photo_detector import PhotoDetector
from tampering_detection.detectors.text_detector import TextDetector
from tampering_detection.detectors.stamp_detector import StampDetector
from tampering_detection.detectors.duplicate_detector import DuplicateDetector

__all__ = [
    "BaseDetector",
    "MetadataDetector",
    "ElaDetector",
    "PhotoDetector",
    "TextDetector",
    "StampDetector",
    "DuplicateDetector",
]
