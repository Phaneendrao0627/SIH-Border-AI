"""Module 3: Tampering Detection for AI-Based Fake Identity & Document Screening System.

Standalone digital image-forensics and physical document tampering detection module.
"""

from tampering_detection.api import analyze_document
from tampering_detection.config import DetectionConfig
from tampering_detection.exceptions import (
    ConfigurationError,
    DetectorExecutionError,
    ImageFormatError,
    ImageLoadError,
    ImageSizeError,
    InvalidRegionError,
    MetadataExtractionError,
    TamperingDetectionError,
)
from tampering_detection.schemas import (
    DocumentRegions,
    EvidenceItem,
    ImageQualityMetrics,
    RegionCoordinate,
    RiskLevel,
    SeverityLevel,
    TamperingDetectionResult,
)

__version__ = "1.0.0"

__all__ = [
    "analyze_document",
    "DetectionConfig",
    "DocumentRegions",
    "RegionCoordinate",
    "TamperingDetectionResult",
    "RiskLevel",
    "SeverityLevel",
    "EvidenceItem",
    "ImageQualityMetrics",
    "TamperingDetectionError",
    "ImageLoadError",
    "ImageFormatError",
    "ImageSizeError",
    "InvalidRegionError",
    "MetadataExtractionError",
    "DetectorExecutionError",
    "ConfigurationError",
]
