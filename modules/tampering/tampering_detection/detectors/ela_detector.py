"""Error Level Analysis (ELA) forensic detector."""

import io
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image

from tampering_detection.config import DetectionConfig
from tampering_detection.detectors.base import BaseDetector
from tampering_detection.io.image_loader import LoadedImage
from tampering_detection.logging_config import get_logger
from tampering_detection.schemas import (
    DocumentRegions,
    ElaAnalysisResult,
    EvidenceItem,
    SeverityLevel,
)

logger = get_logger("detectors.ela")


class ElaDetector(BaseDetector):
    """Detects compression inconsistencies across document regions using Error Level Analysis."""

    def __init__(self):
        super().__init__(name="ela_analysis")

    def compute_ela_maps(
        self,
        image_pil: Image.Image,
        quality: int = 90,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Compute raw pixel difference and scaled grayscale ELA intensity map.

        Args:
            image_pil: PIL Image in RGB format.
            quality: JPEG recompression quality level (default 90).

        Returns:
            Tuple of (diff_rgb [H, W, 3], ela_gray [H, W]).
        """
        # 1. Recompress in memory at specified JPEG quality
        buffer = io.BytesIO()
        image_pil.convert("RGB").save(buffer, format="JPEG", quality=quality)
        buffer.seek(0)
        recompressed = Image.open(buffer).convert("RGB")

        orig_arr = np.array(image_pil.convert("RGB"), dtype=np.float32)
        recomp_arr = np.array(recompressed, dtype=np.float32)

        # 2. Absolute pixel difference
        diff = np.abs(orig_arr - recomp_arr)

        # 3. Grayscale intensity map (mean across channels)
        ela_gray = np.mean(diff, axis=2)

        return diff, ela_gray

    def run(
        self,
        image: LoadedImage,
        regions: DocumentRegions,
        config: DetectionConfig,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[ElaAnalysisResult, List[EvidenceItem], List[str], Dict[str, Any]]:
        """Execute Error Level Analysis.

        Returns:
            Tuple of (ElaAnalysisResult, List[EvidenceItem], List[str] warnings, context_dict).
        """
        warnings: List[str] = []
        evidence: List[EvidenceItem] = []
        anomaly_regions: List[str] = []

        # Check reliability flags
        is_png_or_scan = image.original_format in ("PNG", "TIFF")
        if is_png_or_scan:
            warnings.append(
                "ELA_NOT_RELIABLE: Image originates from a lossless or scan format (PNG/TIFF). "
                "Error level analysis produces higher false positive rates on non-JPEG baselines."
            )

        # 1. Compute ELA difference
        diff_rgb, ela_gray = self.compute_ela_maps(image.pil_image, quality=config.ela_jpeg_quality)

        # 2. Statistical calculation
        g_mean = float(np.mean(ela_gray))
        g_median = float(np.median(ela_gray))
        g_std = float(np.std(ela_gray))
        g_p90 = float(np.percentile(ela_gray, 90))
        g_p95 = float(np.percentile(ela_gray, 95))
        g_max = float(np.max(ela_gray))

        # 3. Connected component analysis on high-error regions
        threshold = g_mean + config.ela_anomaly_sigma * max(g_std, 1.0)
        high_error_mask = (ela_gray > threshold).astype(np.uint8)

        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
            high_error_mask, connectivity=8
        )

        significant_components = 0
        total_anomaly_pixels = 0
        min_size = config.ela_min_component_size

        for i in range(1, num_labels):
            area = stats[i, cv2.CC_STAT_AREA]
            if area >= min_size:
                significant_components += 1
                total_anomaly_pixels += area

        anomaly_ratio = total_anomaly_pixels / float(ela_gray.size)

        # 4. Regional ELA evaluation for provided regions
        all_regions = regions.photo + regions.text + regions.stamp
        regional_ela_stats: Dict[str, Dict[str, float]] = {}

        for reg in all_regions:
            x1 = max(0, min(reg.x, image.width - 1))
            y1 = max(0, min(reg.y, image.height - 1))
            x2 = min(image.width, x1 + reg.width)
            y2 = min(image.height, y1 + reg.height)

            crop = ela_gray[y1:y2, x1:x2]
            if crop.size > 0:
                r_mean = float(np.mean(crop))
                r_std = float(np.std(crop))
                r_p95 = float(np.percentile(crop, 95))
                regional_ela_stats[reg.name] = {
                    "mean": r_mean,
                    "std": r_std,
                    "p95": r_p95,
                    "diff_from_global": r_mean - g_mean,
                }

                # If region mean or p95 deviates substantially from document baseline
                if (r_mean - g_mean) > (1.8 * max(g_std, 2.0)) or (r_p95 - g_p95) > (2.2 * max(g_std, 2.0)):
                    anomaly_regions.append(reg.name)

        # 5. Global ELA Score formulation
        # Higher score reflects pronounced localized error clusters deviating from baseline
        raw_score = 0.0
        if significant_components > 0:
            component_factor = min(35.0, significant_components * 5.0)
            ratio_factor = min(35.0, anomaly_ratio * 700.0)
            variance_factor = min(30.0, (g_std / max(g_mean, 1.0)) * 20.0)
            raw_score = component_factor + ratio_factor + variance_factor

        if anomaly_regions:
            raw_score = max(raw_score, 45.0 + min(35.0, len(anomaly_regions) * 15.0))

        ela_score = round(min(100.0, max(0.0, raw_score)), 1)

        # 6. Generate Explainable Evidence
        if ela_score >= 40.0:
            severity = (
                SeverityLevel.HIGH
                if ela_score >= 70.0
                else SeverityLevel.MEDIUM
            )
            evidence.append(
                self.create_evidence(
                    signal="compression_error_level_anomaly",
                    severity=severity,
                    score_contribution=ela_score,
                    description=(
                        f"Error Level Analysis detected localized compression inconsistencies "
                        f"across {significant_components} cluster(s). Affected regions: "
                        f"{', '.join(anomaly_regions) if anomaly_regions else 'unsegmented areas'}."
                    ),
                    measurements={
                        "global_mean": round(g_mean, 2),
                        "global_std": round(g_std, 2),
                        "global_p95": round(g_p95, 2),
                        "significant_clusters": significant_components,
                        "anomaly_pixel_ratio": round(anomaly_ratio, 4),
                        "flagged_regions": anomaly_regions,
                    },
                    confidence=0.68 if is_png_or_scan else 0.82,
                )
            )

        result = ElaAnalysisResult(
            enabled=True,
            quality=config.ela_jpeg_quality,
            global_mean=round(g_mean, 2),
            global_std=round(g_std, 2),
            global_p95=round(g_p95, 2),
            score=ela_score,
            anomaly_regions=anomaly_regions,
            limitations=[
                "ELA is a forensic heuristic and may produce false positives after multiple saves, resizing, or scanning.",
                "Lossless formats like PNG and TIFF do not have native JPEG quantization baselines.",
            ],
        )

        ela_context = {
            "ela_gray": ela_gray,
            "diff_rgb": diff_rgb,
            "global_mean": g_mean,
            "global_std": g_std,
            "regional_ela_stats": regional_ela_stats,
        }

        return result, evidence, warnings, ela_context
