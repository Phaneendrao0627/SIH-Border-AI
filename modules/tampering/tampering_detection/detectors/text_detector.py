"""Text manipulation, stroke consistency, and pixel-density detector."""

from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np

from tampering_detection.config import DetectionConfig
from tampering_detection.detectors.base import BaseDetector
from tampering_detection.io.image_loader import LoadedImage
from tampering_detection.logging_config import get_logger
from tampering_detection.preprocessing.image_normalization import safe_crop_region
from tampering_detection.schemas import (
    DocumentRegions,
    EvidenceItem,
    RegionForensicDetail,
    SeverityLevel,
    TextAnalysisResult,
)

logger = get_logger("detectors.text")


class TextDetector(BaseDetector):
    """Forensic detector analyzing text fields for stroke anomalies, density variance, and paste artifacts."""

    def __init__(self):
        super().__init__(name="text_analysis")

    def _analyze_text_region(
        self,
        gray_crop: np.ndarray,
    ) -> Dict[str, Any]:
        """Extract morphological and structural text features from a cropped text region."""
        h, w = gray_crop.shape
        total_pixels = float(h * w) if (h * w) > 0 else 1.0

        # Otsu thresholding for foreground separation (assuming dark text on lighter paper)
        # Invert so text characters are foreground (255)
        _, bin_inv = cv2.threshold(gray_crop, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # Foreground pixel density
        fg_pixels = np.count_nonzero(bin_inv)
        pixel_density = fg_pixels / total_pixels

        # Canny edge density
        edges = cv2.Canny(gray_crop, 50, 150)
        edge_density = np.count_nonzero(edges) / total_pixels

        # Stroke width estimation via Distance Transform on foreground text
        stroke_mean = 0.0
        stroke_std = 0.0
        if fg_pixels > 10:
            dist_transform = cv2.distanceTransform(bin_inv, cv2.DIST_L2, 3)
            # Skeleton strokes correspond to ridge peaks in distance transform
            foreground_dist = dist_transform[bin_inv > 0]
            if foreground_dist.size > 0:
                stroke_mean = float(np.mean(foreground_dist) * 2.0)  # full stroke diameter approx
                stroke_std = float(np.std(foreground_dist) * 2.0)

        # Connected component statistics
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(bin_inv, connectivity=8)
        char_count = max(0, num_labels - 1)

        # Local contrast between foreground and background
        bg_mask = (bin_inv == 0)
        fg_mask = (bin_inv > 0)
        bg_mean = float(np.mean(gray_crop[bg_mask])) if np.count_nonzero(bg_mask) > 0 else 255.0
        fg_mean = float(np.mean(gray_crop[fg_mask])) if np.count_nonzero(fg_mask) > 0 else 0.0
        contrast = max(0.0, bg_mean - fg_mean)

        # Abrupt rectangular edit boundary check:
        # Check standard deviation along extreme outer border of the text box (patch artifact)
        border_pixels = np.concatenate([
            gray_crop[0, :],
            gray_crop[-1, :],
            gray_crop[:, 0],
            gray_crop[:, -1],
        ])
        border_std = float(np.std(border_pixels))
        pure_white_ratio = float(np.mean(gray_crop >= 250))
        has_flat_patch = bool(
            ((border_std < 0.8) and (pixel_density > 0.05))
            or (pure_white_ratio > 0.12)
        )

        return {
            "pixel_density": round(pixel_density, 3),
            "edge_density": round(edge_density, 3),
            "stroke_mean": round(stroke_mean, 2),
            "stroke_std": round(stroke_std, 2),
            "char_count": char_count,
            "contrast": round(contrast, 2),
            "has_flat_patch": has_flat_patch,
        }

    def run(
        self,
        image: LoadedImage,
        regions: DocumentRegions,
        config: DetectionConfig,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[TextAnalysisResult, List[EvidenceItem], List[str]]:
        """Execute text tampering analysis across specified regions.

        Returns:
            Tuple of (TextAnalysisResult, List[EvidenceItem], List[str] warnings).
        """
        warnings: List[str] = []
        evidence: List[EvidenceItem] = []

        if not regions.text:
            result = TextAnalysisResult(
                enabled=False,
                regions_analyzed=0,
                text_manipulation_suspected=False,
                score=None,
                confidence=None,
                signals=[],
                region_results=[],
                reason="No text coordinates were provided.",
            )
            return result, evidence, warnings

        region_details: List[RegionForensicDetail] = []
        extracted_features: List[Dict[str, Any]] = []
        aggregated_signals: List[str] = []
        highest_score = 0.0
        total_confidence = 0.0

        ela_stats = (context or {}).get("regional_ela_stats", {})
        global_ela_mean = (context or {}).get("global_mean", 0.0)

        # 1. Feature extraction per region
        for text_reg in regions.text:
            reg_signals: List[str] = []
            reg_warnings: List[str] = []
            reg_score = 0.0
            reg_conf = 0.80

            crop_gray = safe_crop_region(image.gray_array, text_reg)

            if crop_gray.shape[0] < config.text_min_region_height or crop_gray.shape[1] < config.text_min_region_width:
                reg_warnings.append("REGION_TOO_SMALL: Text crop is too small for reliable stroke modeling.")
                reg_conf = 0.40
                features = {
                    "pixel_density": 0.0,
                    "edge_density": 0.0,
                    "stroke_mean": 0.0,
                    "stroke_std": 0.0,
                    "char_count": 0,
                    "contrast": 0.0,
                    "has_flat_patch": False,
                }
            else:
                features = self._analyze_text_region(crop_gray)

            # Local anomaly: flat paste patch
            if features.get("has_flat_patch"):
                reg_signals.append("rectangular_paste_boundary")
                reg_score += 35.0

            # ELA anomaly in text region
            reg_ela = ela_stats.get(text_reg.name)
            if reg_ela:
                ela_diff = reg_ela.get("mean", 0.0) - global_ela_mean
                if ela_diff > config.text_ela_diff_threshold:
                    reg_signals.append("compression_anomaly")
                    reg_score += 25.0

            extracted_features.append(features)

            region_details.append(
                RegionForensicDetail(
                    region_name=text_reg.name,
                    tampering_score=round(min(100.0, reg_score), 1),
                    confidence=round(reg_conf, 2),
                    signals=reg_signals,
                    measurements=features,
                    warnings=reg_warnings,
                    evidence_summary=(
                        f"Region '{text_reg.name}' analyzed. Density: {features['pixel_density']}, "
                        f"Stroke: {features['stroke_mean']}px."
                    ),
                )
            )

        # 2. Cross-Region Consistency Analysis (only if >= 2 regions)
        if len(regions.text) >= 2:
            densities = [f["pixel_density"] for f in extracted_features if f["pixel_density"] > 0]
            strokes = [f["stroke_mean"] for f in extracted_features if f["stroke_mean"] > 0]

            if len(densities) >= 2:
                mean_density = float(np.mean(densities))
                for idx, detail in enumerate(region_details):
                    f = extracted_features[idx]
                    if f["pixel_density"] > 0 and abs(f["pixel_density"] - mean_density) > config.text_density_delta_threshold:
                        if "pixel_density_inconsistency" not in detail.signals:
                            detail.signals.append("pixel_density_inconsistency")
                            detail.tampering_score = min(100.0, detail.tampering_score + 30.0)

            if len(strokes) >= 2:
                mean_stroke = float(np.mean(strokes))
                for idx, detail in enumerate(region_details):
                    f = extracted_features[idx]
                    if f["stroke_mean"] > 0 and abs(f["stroke_mean"] - mean_stroke) / max(mean_stroke, 0.5) > config.text_stroke_variance_threshold:
                        if "stroke_width_inconsistency" not in detail.signals:
                            detail.signals.append("stroke_width_inconsistency")
                            detail.tampering_score = min(100.0, detail.tampering_score + 30.0)

        else:
            warnings.append(
                "INSUFFICIENT_EVIDENCE: Only 1 text region supplied; cross-field typography consistency "
                "comparison was skipped."
            )

        # 3. Aggregate evidence and signals
        for detail in region_details:
            highest_score = max(highest_score, detail.tampering_score)
            total_confidence += detail.confidence
            for s in detail.signals:
                if s not in aggregated_signals:
                    aggregated_signals.append(s)

            if detail.tampering_score >= 30.0:
                evidence.append(
                    self.create_evidence(
                        signal="text_manipulation_suspected" if detail.signals else "typography_anomaly",
                        severity=SeverityLevel.MEDIUM if detail.tampering_score < 70 else SeverityLevel.HIGH,
                        score_contribution=detail.tampering_score,
                        description=(
                            f"Text region '{detail.region_name}' exhibits forensic anomalies: "
                            f"{', '.join(detail.signals)}. This suggests possible digital alteration."
                        ),
                        measurements=detail.measurements,
                        confidence=detail.confidence,
                        region_name=detail.region_name,
                    )
                )

        avg_confidence = round(total_confidence / len(regions.text), 2) if regions.text else 0.0
        suspected = (highest_score >= 50.0) or (len(aggregated_signals) >= 2)

        result = TextAnalysisResult(
            enabled=True,
            regions_analyzed=len(regions.text),
            text_manipulation_suspected=suspected,
            score=round(highest_score, 1),
            confidence=avg_confidence,
            signals=aggregated_signals,
            region_results=region_details,
            reason=None,
        )

        return result, evidence, warnings
