"""Module 3: Tampering Detection package for SIH-Border-AI."""

import sys
from pathlib import Path

# Ensure this directory is in sys.path
_MODULE_DIR = Path(__file__).resolve().parent
if str(_MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(_MODULE_DIR))

from tampering_detection import (
    analyze_document,
    DetectionConfig,
    DocumentRegions,
    RegionCoordinate,
    TamperingDetectionResult,
    RiskLevel,
    SeverityLevel,
)
from .module3 import analyze_tampering

__all__ = [
    "analyze_tampering",
    "analyze_document",
    "DetectionConfig",
    "DocumentRegions",
    "RegionCoordinate",
    "TamperingDetectionResult",
    "RiskLevel",
    "SeverityLevel",
]
