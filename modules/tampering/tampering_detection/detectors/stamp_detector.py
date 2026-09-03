"""Stamp forgery, texture consistency, and duplicated stamp detector."""

from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
from skimage.feature import graycomatrix, graycoprops, local_binary_pattern
from skimage.measure import shannon_entropy

from tampering_detection.config import DetectionConfig
from tampering_detection.detectors.base import BaseDetector
from tampering_detection.detectors.duplicate_detector import DuplicateDetector
from tampering_detection.io.image_loader import LoadedImage
from tampering_detection.logging_config import get_logger
from tampering_detection.preprocessing.image_normalization import safe_crop_region
from tampering_detection.schemas import (
    DocumentRegions,
    EvidenceItem,
    RegionForensicDetail,
    SeverityLevel,
    StampAnalysisResult,
)

logger = get_logger("detectors.stamp")


class StampDetector(BaseDetector):
    """Forensic detector identifying forged, cloned, or digitally stamped seals."""

    def __init__(self):
        super().__init__(name="stamp_analysis")
        self.duplicate_detector = DuplicateDetector()

    def _analyze_texture(self, gray_crop: np.ndarray, config: DetectionConfig) -> Dict[str, Any]:
        """Compute LBP, entropy, and GLCM texture features."""
        h, w = gray_crop.shape

        # 1. Shannon Entropy
        entropy_val = float(shannon_entropy(gray_crop))

        # 2. Local Binary Patterns
        lbp = local_binary_pattern(
            gray_crop,
            P=config.stamp_lbp_points,
            R=config.stamp_lbp_radius,
            method="uniform",
        )
        n_bins = config.stamp_lbp_points + 2
        lbp_hist, _ = np.histogram(lbp.ravel(), bins=n_bins, range=(0, n_bins), density=True)
        lbp_uniformity = float(np.sum(lbp_hist**2))

        # 3. GLCM features (if size permits)
        glcm_contrast = 0.0
        glcm_homogeneity = 0.0
        if h >= 25 and w >= 25:
            try:
                glcm = graycomatrix(
                    gray_crop,
                    distances=[1],
                    angles=[0, np.pi / 4, np.pi / 2],
                    levels=256,
                    symmetric=True,
                    normed=True,
                )
                glcm_contrast = float(np.mean(graycoprops(glcm, "contrast")))
                glcm_homogeneity = float(np.mean(graycoprops(glcm, "homogeneity")))
            except Exception as e:
                logger.debug("GLCM extraction skipped: %s", e)

        # 4. Background flatness check
        # Otsu to segment stamp ink from surrounding background
        _, bin_ink = cv2.threshold(gray_crop, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        bg_pixels = gray_crop[bin_ink == 0]
        bg_std = float(np.std(bg_pixels)) if len(bg_pixels) > 20 else 25.0

        is_flat_bg = bg_std < config.stamp_flat_background_threshold

        return {
            "entropy": round(entropy_val, 3),
            "lbp_uniformity": round(lbp_uniformity, 3),
            "glcm_contrast": round(glcm_contrast, 2),
            "glcm_homogeneity": round(glcm_homogeneity, 3),
            "background_std": round(bg_std, 2),
            "is_flat_background": is_flat_bg,
        }

    def run(
        self,
        image: LoadedImage,
        regions: DocumentRegions,
        config: DetectionConfig,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[StampAnalysisResult, List[EvidenceItem], List[str]]:
        """Execute stamp forgery and texture analysis.

        Returns:
            Tuple of (StampAnalysisResult, List[EvidenceItem], List[str] warnings).
        """
        warnings: List[str] = []
        evidence: List[EvidenceItem] = []

        if not regions.stamp:
            result = StampAnalysisResult(
                enabled=False,
                regions_analyzed=0,
                stamp_forgery_suspected=False,
                score=None,
                texture_anomaly_score=None,
                duplicate_pattern_score=None,
                ela_anomaly_score=None,
                confidence=None,
                signals=[],
                region_results=[],
                reason="No stamp coordinates were provided.",
            )
            return result, evidence, warnings

        region_details: List[RegionForensicDetail] = []
        aggregated_signals: List[str] = []
        max_texture_score = 0.0
        max_dup_score = 0.0
        max_ela_score = 0.0
        highest_score = 0.0
        total_confidence = 0.0

        ela_stats = (context or {}).get("regional_ela_stats", {})
        global_ela_mean = (context or {}).get("global_mean", 0.0)

        # 1. Per-stamp region evaluation
        stamp_crops_rgb: List[np.ndarray] = []
        stamp_crops_gray: List[np.ndarray] = []

        for stamp_reg in regions.stamp:
            reg_signals: List[str] = []
            reg_warnings: List[str] = []
            reg_score = 0.0
            reg_conf = 0.80

            crop_rgb = safe_crop_region(image.rgb_array, stamp_reg)
            crop_gray = safe_crop_region(image.gray_array, stamp_reg)
            stamp_crops_rgb.append(crop_rgb)
            stamp_crops_gray.append(crop_gray)

            texture_metrics = self._analyze_texture(crop_gray, config)

            # Flat pasted background
            if texture_metrics.get("is_flat_background"):
                reg_signals.append("flat_pasted_background")
                reg_score += 30.0
                max_texture_score = max(max_texture_score, 30.0)

            # Perimeter rectangular edge artifact
            border_edges = cv2.Canny(crop_gray, 50, 150)
            perimeter_pixels = np.concatenate([
                border_edges[0, :],
                border_edges[-1, :],
                border_edges[:, 0],
                border_edges[:, -1],
            ])
            edge_ratio = np.count_nonzero(perimeter_pixels) / float(len(perimeter_pixels)) if len(perimeter_pixels) > 0 else 0
            if edge_ratio > 0.40:
                reg_signals.append("suspicious_rectangular_stamp_boundary")
                reg_score += 25.0

            # ELA anomaly
            reg_ela = ela_stats.get(stamp_reg.name)
            if reg_ela:
                ela_diff = reg_ela.get("mean", 0.0) - global_ela_mean
                if ela_diff > 8.0:
                    reg_signals.append("stamp_ela_anomaly")
                    reg_score += 25.0
                    max_ela_score = max(max_ela_score, 25.0)

            # Check duplicate against full document
            is_dup, dup_score, loc = self.duplicate_detector.find_duplicate_in_document(
                crop_gray, image.gray_array, stamp_reg, match_threshold=config.duplicate_template_threshold
            )
            if is_dup:
                reg_signals.append("possible_duplicated_pattern")
                reg_score += 45.0
                max_dup_score = max(max_dup_score, 45.0)
                evidence.append(
                    self.create_evidence(
                        signal="possible_duplicated_pattern",
                        severity=SeverityLevel.HIGH,
                        score_contribution=45.0,
                        description=(
                            f"Stamp region '{stamp_reg.name}' matches another region in the document "
                            f"with high correlation ({round(dup_score, 2)}), indicating possible copy-paste duplication."
                        ),
                        measurements={"match_score": round(dup_score, 3), "duplicate_location": loc},
                        confidence=0.85,
                        region_name=stamp_reg.name,
                    )
                )

            final_reg_score = min(100.0, reg_score)
            highest_score = max(highest_score, final_reg_score)
            total_confidence += reg_conf

            for s in reg_signals:
                if s not in aggregated_signals:
                    aggregated_signals.append(s)

            region_details.append(
                RegionForensicDetail(
                    region_name=stamp_reg.name,
                    tampering_score=round(final_reg_score, 1),
                    confidence=round(reg_conf, 2),
                    signals=reg_signals,
                    measurements=texture_metrics,
                    warnings=reg_warnings,
                    evidence_summary=(
                        f"Stamp region '{stamp_reg.name}' analyzed. Entropy: {texture_metrics['entropy']}, "
                        f"Signals: {', '.join(reg_signals) if reg_signals else 'none'}."
                    ),
                )
            )

        # 2. Cross-stamp perceptual comparison (if >= 2 stamps provided)
        if len(regions.stamp) >= 2:
            for i in range(len(regions.stamp)):
                for j in range(i + 1, len(regions.stamp)):
                    is_dup, dist, sim = self.duplicate_detector.compare_regions_perceptual(
                        stamp_crops_rgb[i],
                        stamp_crops_rgb[j],
                        hash_threshold=config.duplicate_hash_threshold,
                    )
                    if is_dup:
                        reg_i_name = regions.stamp[i].name
                        reg_j_name = regions.stamp[j].name
                        signal_name = "identical_stamp_duplicate"
                        if signal_name not in aggregated_signals:
                            aggregated_signals.append(signal_name)
                        max_dup_score = max(max_dup_score, 50.0)
                        highest_score = max(highest_score, 65.0)

                        evidence.append(
                            self.create_evidence(
                                signal=signal_name,
                                severity=SeverityLevel.HIGH,
                                score_contribution=50.0,
                                description=(
                                    f"Stamps '{reg_i_name}' and '{reg_j_name}' share nearly identical perceptual "
                                    f"signatures (Hamming distance {dist}), suggesting visual cloning."
                                ),
                                measurements={"hamming_distance": dist, "perceptual_similarity": round(sim, 2)},
                                confidence=0.88,
                                region_name=reg_i_name,
                            )
                        )

        # 3. Compile evidence for texture/boundary if flagged
        if "flat_pasted_background" in aggregated_signals:
            evidence.append(
                self.create_evidence(
                    signal="flat_pasted_background",
                    severity=SeverityLevel.MEDIUM,
                    score_contribution=30.0,
                    description=(
                        "Stamp substrate exhibits unnaturally uniform background variance, "
                        "consistent with digital cutout and pasting onto document background."
                    ),
                    measurements={"texture_anomaly_score": round(max_texture_score, 1)},
                    confidence=0.75,
                )
            )

        avg_confidence = round(total_confidence / len(regions.stamp), 2) if regions.stamp else 0.0
        suspected = (highest_score >= 45.0) or (len(aggregated_signals) >= 2)

        result = StampAnalysisResult(
            enabled=True,
            regions_analyzed=len(regions.stamp),
            stamp_forgery_suspected=suspected,
            score=round(highest_score, 1),
            texture_anomaly_score=round(max_texture_score, 1),
            duplicate_pattern_score=round(max_dup_score, 1),
            ela_anomaly_score=round(max_ela_score, 1),
            confidence=avg_confidence,
            signals=aggregated_signals,
            region_results=region_details,
            reason=None,
        )

        return result, evidence, warnings
