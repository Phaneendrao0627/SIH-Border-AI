"""Base class for all tampering forensic detectors."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from tampering_detection.config import DetectionConfig
from tampering_detection.io.image_loader import LoadedImage
from tampering_detection.schemas import DocumentRegions, EvidenceItem, SeverityLevel


class BaseDetector(ABC):
    """Abstract base class establishing standard detector interface."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def run(
        self,
        image: LoadedImage,
        regions: DocumentRegions,
        config: DetectionConfig,
        context: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Execute forensic analysis on the provided image and regions.

        Args:
            image: Loaded and normalized image.
            regions: Validated document regions.
            config: Detection configuration.
            context: Shared inter-detector context (e.g., global ELA statistics).

        Returns:
            Detector-specific result model.
        """
        raise NotImplementedError

    def create_evidence(
        self,
        signal: str,
        severity: SeverityLevel,
        score_contribution: float,
        description: str,
        measurements: Dict[str, Any],
        confidence: float,
        region_name: Optional[str] = None,
    ) -> EvidenceItem:
        """Standardized helper to construct explainable forensic evidence records.

        Ensures cautious forensic phrasing.
        """
        return EvidenceItem(
            detector=self.name,
            region_name=region_name,
            signal=signal,
            severity=severity,
            score_contribution=round(float(score_contribution), 2),
            description=description,
            measurements=measurements,
            confidence=round(float(confidence), 2),
        )
