"""Metadata and EXIF forensic detector."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from tampering_detection.config import DetectionConfig
from tampering_detection.detectors.base import BaseDetector
from tampering_detection.io.image_loader import LoadedImage
from tampering_detection.io.metadata_reader import extract_metadata
from tampering_detection.logging_config import get_logger
from tampering_detection.schemas import (
    DocumentRegions,
    EvidenceItem,
    MetadataAnalysisResult,
    SeverityLevel,
)

logger = get_logger("detectors.metadata")


class MetadataDetector(BaseDetector):
    """Forensic detector analyzing image EXIF tags for software signatures and temporal inconsistencies."""

    def __init__(self):
        super().__init__(name="metadata_analysis")

    def run(
        self,
        image: LoadedImage,
        regions: DocumentRegions,
        config: DetectionConfig,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[MetadataAnalysisResult, List[EvidenceItem], List[str]]:
        """Run metadata analysis.

        Returns:
            Tuple of (MetadataAnalysisResult, List[EvidenceItem], List[str] warnings).
        """
        available, safe_tags, timestamps, reader_warnings = extract_metadata(
            raw_bytes=image.raw_bytes,
            pil_image=image.pil_image,
        )

        flags: List[str] = []
        warnings: List[str] = list(reader_warnings)
        evidence: List[EvidenceItem] = []
        detected_software: Optional[str] = None
        score = 0.0

        if not available or len(safe_tags) == 0:
            flags.append("metadata_unavailable")
            flags.append("metadata_stripped_or_minimal")
            warnings.append("METADATA_UNAVAILABLE: Image carries no EXIF tags (common in scans, web uploads, or messaging exports).")
            # Stripped/missing metadata generates a warning/flag, not a high tampering score
            result = MetadataAnalysisResult(
                available=False,
                flags=flags,
                software=None,
                timestamps=timestamps,
                raw_safe_tags={},
                score=0.0,
            )
            return result, evidence, warnings

        # 1. Search for editing software in tags
        for key, val in safe_tags.items():
            val_str = str(val).lower()
            for kw in config.suspicious_software_keywords:
                if kw in val_str:
                    detected_software = str(val)
                    if "editing_software_detected" not in flags:
                        flags.append("editing_software_detected")
                        flags.append("suspicious_software_string")
                    score = max(score, 45.0)
                    break
            if detected_software:
                break

        if detected_software:
            evidence.append(
                self.create_evidence(
                    signal="editing_software_detected",
                    severity=SeverityLevel.MEDIUM,
                    score_contribution=45.0,
                    description=(
                        f"Image metadata indicates processing or export by image editing software: "
                        f"'{detected_software}'. This heuristic indicates digital manipulation history."
                    ),
                    measurements={"software_tag": detected_software},
                    confidence=0.85,
                )
            )

        # 2. Check for timestamp discrepancies
        dt_orig = timestamps.get("DateTimeOriginal")
        dt_mod = timestamps.get("DateTime") or timestamps.get("ModifyDate")
        if dt_orig and dt_mod and dt_orig != dt_mod:
            try:
                # Format: "YYYY:MM:DD HH:MM:SS"
                fmt = "%Y:%m:%d %H:%M:%S"
                d1 = datetime.strptime(dt_orig.strip(), fmt)
                d2 = datetime.strptime(dt_mod.strip(), fmt)
                delta_hours = abs((d2 - d1).total_seconds()) / 3600.0
                if delta_hours > 24.0:
                    flags.append("timestamp_inconsistency")
                    score = min(score + 15.0, 50.0)
                    evidence.append(
                        self.create_evidence(
                            signal="timestamp_inconsistency",
                            severity=SeverityLevel.LOW,
                            score_contribution=15.0,
                            description=(
                                f"Discrepancy detected between original capture timestamp ({dt_orig}) "
                                f"and modification timestamp ({dt_mod})."
                            ),
                            measurements={"original_timestamp": dt_orig, "modify_timestamp": dt_mod, "delta_hours": delta_hours},
                            confidence=0.70,
                        )
                    )
            except Exception:
                pass

        # 3. Check for dimension discrepancies between EXIF and image array
        exif_w = safe_tags.get("EXIF ExifImageWidth")
        exif_h = safe_tags.get("EXIF ExifImageLength")
        if exif_w and exif_h:
            try:
                ew = int(str(exif_w))
                eh = int(str(exif_h))
                if (ew != image.width or eh != image.height) and (ew != image.height or eh != image.width):
                    flags.append("inconsistent_dimensions")
                    score = min(score + 15.0, 50.0)
                    evidence.append(
                        self.create_evidence(
                            signal="inconsistent_dimensions",
                            severity=SeverityLevel.LOW,
                            score_contribution=15.0,
                            description=(
                                f"EXIF reported dimensions ({ew}x{eh}) do not match actual "
                                f"image pixel dimensions ({image.width}x{image.height})."
                            ),
                            measurements={"exif_width": ew, "exif_height": eh, "actual_width": image.width, "actual_height": image.height},
                            confidence=0.65,
                        )
                    )
            except Exception:
                pass

        # Strictly enforce safety rule: metadata alone cannot exceed 50.0 (cannot cause HIGH or CRITICAL risk)
        final_score = min(score, 50.0)

        result = MetadataAnalysisResult(
            available=available,
            flags=flags,
            software=detected_software,
            timestamps=timestamps,
            raw_safe_tags=safe_tags,
            score=round(final_score, 2),
        )

        return result, evidence, warnings
