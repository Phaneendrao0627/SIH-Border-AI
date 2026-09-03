"""Module 3: Tampering Detection Entrypoint for SIH-Border-AI Central Pipeline."""

import sys
from pathlib import Path
from typing import Any, Dict, Optional, Union

# Ensure tampering module directory is on sys.path
_MODULE_DIR = Path(__file__).resolve().parent
if str(_MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(_MODULE_DIR))

from tampering_detection.api import analyze_document
from tampering_detection.config import DetectionConfig
from tampering_detection.schemas import TamperingDetectionResult


def analyze_tampering(
    image_path: Union[str, Path],
    regions: Optional[Dict[str, Any]] = None,
    document_id: Optional[str] = None,
    document_type: str = "passport",
    options: Optional[Union[Dict[str, Any], DetectionConfig]] = None,
) -> Dict[str, Any]:
    """Execute complete Module 3 tampering detection pipeline.

    Compatible with FastAPI backend and orchestrator pipeline.

    Args:
        image_path: File path, bytes, BytesIO, PIL Image, or NumPy array.
        regions: Optional dictionary with 'photo', 'text', 'stamp' coordinates.
        document_id: Optional document identifier string.
        document_type: Category (e.g. 'passport', 'visa', 'id_card').
        options: Optional DetectionConfig or dictionary overrides.

    Returns:
        Python dictionary conforming to standard forensic result schema.
    """
    result = analyze_document(
        image_source=image_path,
        document_id=document_id,
        document_type=document_type,
        regions=regions,
        options=options,
    )
    return result.model_dump()


__all__ = [
    "analyze_tampering",
    "analyze_document",
    "DetectionConfig",
    "TamperingDetectionResult",
]
