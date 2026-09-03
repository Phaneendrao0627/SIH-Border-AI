"""Photo replacement and portrait tampering detector."""

from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np

from tampering_detection.config import DetectionConfig
from tampering_detection.detectors.base import BaseDetector
from tampering_detection.io.image_loader import LoadedImage
from tampering_detection.logging_config import get_logger
from tampering_detection.preprocessing.image_normalization import (
    extract_border_strips,
    extract_surrounding_background,
    safe_crop_region,
)
from tampering_detection.schemas import (
    DocumentRegions,
    EvidenceItem,
    PhotoAnalysisResult,
    RegionForensicDetail,
    SeverityLevel,
)

logger = get_logger("detectors.photo")


class PhotoDetector(BaseDetector):
    """Forensic detector identifying spliced, replaced, or manipulated portrait photos."""

    def __init__(self):
        super().__init__(name="photo_analysis")

    def _estimate_noise(self, gray_crop: np.ndarray) -> Tuple[float, float]:
        """Estimate high-frequency noise standard deviation and MAD using Laplacian residuals on non-edge pixels."""
        if gray_crop.size < 25:
            return 0.0, 0.0
        # High frequency residual
        blurred = cv2.GaussianBlur(gray_crop, (3, 3), 0)
        residual = gray_crop.astype(np.float32) - blurred.astype(np.float32)

        # Gradient mask to isolate homogeneous substrate and avoid object contours
        grad = cv2.magnitude(
            cv2.Sobel(gray_crop, cv2.CV_32F, 1, 0, ksize=3),
            cv2.Sobel(gray_crop, cv2.CV_32F, 0, 1, ksize=3),
        )
        non_edge = grad < np.percentile(grad, 75)
        if np.count_nonzero(non_edge) >= 20:
            eval_residual = residual[non_edge]
        else:
            eval_residual = residual

        std_dev = float(np.std(eval_residual))
        mad = float(np.median(np.abs(eval_residual - np.median(eval_residual))))
        return std_dev, mad

    def run(
        self,
        image: LoadedImage,
        regions: DocumentRegions,
        config: DetectionConfig,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[PhotoAnalysisResult, List[EvidenceItem], List[str]]:
        """Run photo replacement analysis.

        Returns:
            Tuple of (PhotoAnalysisResult, List[EvidenceItem], List[str] warnings).
        """
        warnings: List[str] = []
        evidence: List[EvidenceItem] = []

        if not regions.photo:
            result = PhotoAnalysisResult(
                enabled=False,
                regions_analyzed=0,
                photo_replacement_suspected=False,
                score=None,
                confidence=None,
                signals=[],
                region_results=[],
                reason="No photo coordinates were provided.",
            )
            return result, evidence, warnings

        region_details: List[RegionForensicDetail] = []
        aggregated_signals: List[str] = []
        highest_score = 0.0
        total_confidence = 0.0

        ela_stats = (context or {}).get("regional_ela_stats", {})
        global_ela_mean = (context or {}).get("global_mean", 0.0)
        global_ela_std = (context or {}).get("global_std", 1.0)

        for photo_reg in regions.photo:
            reg_signals: List[str] = []
            reg_warnings: List[str] = []
            reg_measurements: Dict[str, Any] = {}
            reg_score = 0.0
            reg_conf = 0.85

            # 1. Extract Crops and Boundaries
            photo_crop_rgb = safe_crop_region(image.rgb_array, photo_reg)
            photo_crop_gray = safe_crop_region(image.gray_array, photo_reg)

            # Check for sufficient context
            if photo_crop_gray.shape[0] < 30 or photo_crop_gray.shape[1] < 30:
                reg_warnings.append("INSUFFICIENT_EVIDENCE: Photo crop is too small for reliable boundary and noise modeling.")
                reg_conf = 0.50

            # 2. Boundary Discontinuity Check
            inner_strip, outer_strip = extract_border_strips(
                image.gray_array, photo_reg, strip_width=config.photo_boundary_strip_width
            )

            boundary_gradient_step = 0.0
            if inner_strip is not None and outer_strip is not None:
                mean_inner = float(np.mean(inner_strip))
                mean_outer = float(np.mean(outer_strip))
                boundary_delta = abs(mean_inner - mean_outer)

                # Check gradient magnitude along perimeter
                sobel_x = cv2.Sobel(photo_crop_gray, cv2.CV_32F, 1, 0, ksize=3)
                sobel_y = cv2.Sobel(photo_crop_gray, cv2.CV_32F, 0, 1, ksize=3)
                grad_mag = np.sqrt(sobel_x**2 + sobel_y**2)
                edge_perimeter_mean = float(np.mean(grad_mag))

                reg_measurements["boundary_delta"] = round(boundary_delta, 2)
                reg_measurements["perimeter_gradient"] = round(edge_perimeter_mean, 2)

                if boundary_delta > config.photo_color_delta_threshold or edge_perimeter_mean > 35.0:
                    reg_signals.append("boundary_discontinuity")
                    reg_score += 25.0
            else:
                reg_warnings.append("INSUFFICIENT_CONTEXT: Surrounding document border is too narrow for perimeter analysis.")
                reg_conf = max(0.4, reg_conf - 0.20)

            # 3. Noise Disparity Analysis
            photo_noise_std, photo_mad = self._estimate_noise(photo_crop_gray)
            surrounding_bg = extract_surrounding_background(image.gray_array, photo_reg, ring_thickness=25)

            if surrounding_bg is not None:
                bg_noise_std, bg_mad = self._estimate_noise(surrounding_bg)
                noise_ratio = photo_noise_std / max(bg_noise_std, 0.5)
                reg_measurements["photo_noise_std"] = round(photo_noise_std, 2)
                reg_measurements["surrounding_noise_std"] = round(bg_noise_std, 2)
                reg_measurements["noise_ratio"] = round(noise_ratio, 2)
                reg_measurements["noise_threshold"] = config.photo_noise_ratio_threshold

                # Significant divergence in noise levels between document paper and portrait
                if noise_ratio > config.photo_noise_ratio_threshold or noise_ratio < (1.0 / config.photo_noise_ratio_threshold):
                    reg_signals.append("noise_pattern_mismatch")
                    reg_score += 35.0

                    evidence.append(
                        self.create_evidence(
                            signal="noise_pattern_mismatch",
                            severity=SeverityLevel.MEDIUM,
                            score_contribution=35.0,
                            description=(
                                "The high-frequency noise characteristics inside the photo region differ "
                                "substantially from the immediately surrounding document background, "
                                "suggesting splicing from an alternate camera or scan source."
                            ),
                            measurements={
                                "photo_noise_std": round(photo_noise_std, 2),
                                "surrounding_noise_std": round(bg_noise_std, 2),
                                "noise_ratio": round(noise_ratio, 2),
                                "configured_threshold": config.photo_noise_ratio_threshold,
                            },
                            confidence=round(reg_conf, 2),
                            region_name=photo_reg.name,
                        )
                    )
            else:
                reg_warnings.append("INSUFFICIENT_CONTEXT: Surrounding document background is unavailable for noise comparison.")
                reg_conf = max(0.4, reg_conf - 0.20)

            # 4. Regional ELA Discrepancy
            reg_ela = ela_stats.get(photo_reg.name)
            if reg_ela:
                ela_mean_diff = reg_ela.get("mean", 0.0) - global_ela_mean
                reg_measurements["photo_ela_diff"] = round(ela_mean_diff, 2)
                if ela_mean_diff > max(config.photo_ela_delta_threshold, global_ela_std * 1.5):
                    reg_signals.append("photo_region_ela_deviation")
                    reg_score += 30.0

                    evidence.append(
                        self.create_evidence(
                            signal="photo_region_ela_deviation",
                            severity=SeverityLevel.HIGH if reg_score >= 60 else SeverityLevel.MEDIUM,
                            score_contribution=30.0,
                            description=(
                                f"Photo region '{photo_reg.name}' exhibits significant compression artifact "
                                f"deviation (+{round(ela_mean_diff, 1)}) relative to the document baseline."
                            ),
                            measurements={
                                "region_ela_mean": round(reg_ela.get("mean", 0.0), 2),
                                "global_ela_mean": round(global_ela_mean, 2),
                                "deviation": round(ela_mean_diff, 2),
                            },
                            confidence=round(reg_conf, 2),
                            region_name=photo_reg.name,
                        )
                    )

            # 5. Artificial Occlusion / Solid Blackout Check
            pure_black_ratio = float(np.mean(photo_crop_gray <= 5))
            pure_white_ratio = float(np.mean(photo_crop_gray >= 250))
            if pure_black_ratio > 0.20 or pure_white_ratio > 0.30:
                reg_signals.append("photo_occlusion_or_blackout")
                reg_score += 45.0
                reg_measurements["pure_black_ratio"] = round(pure_black_ratio, 3)
                reg_measurements["pure_white_ratio"] = round(pure_white_ratio, 3)
                evidence.append(
                    self.create_evidence(
                        signal="photo_occlusion_or_blackout",
                        severity=SeverityLevel.HIGH,
                        score_contribution=45.0,
                        description=(
                            f"Photo region '{photo_reg.name}' exhibits an artificial digital occlusion or solid blackout "
                            f"covering {round(max(pure_black_ratio, pure_white_ratio) * 100, 1)}% of the portrait area, obstructing facial biometrics."
                        ),
                        measurements={
                            "pure_black_ratio": round(pure_black_ratio, 3),
                            "pure_white_ratio": round(pure_white_ratio, 3),
                        },
                        confidence=0.95,
                        region_name=photo_reg.name,
                    )
                )

            # 6. Boundary Discontinuity Evidence
            if "boundary_discontinuity" in reg_signals:
                evidence.append(
                    self.create_evidence(
                        signal="boundary_discontinuity",
                        severity=SeverityLevel.MEDIUM,
                        score_contribution=25.0,
                        description=(
                            f"Perimeter analysis of photo region '{photo_reg.name}' shows an abrupt photometric "
                            f"transition and edge gradient discontinuity against the surrounding document substrate."
                        ),
                        measurements=reg_measurements,
                        confidence=round(reg_conf, 2),
                        region_name=photo_reg.name,
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
                    region_name=photo_reg.name,
                    tampering_score=round(final_reg_score, 1),
                    confidence=round(reg_conf, 2),
                    signals=reg_signals,
                    measurements=reg_measurements,
                    warnings=reg_warnings,
                    evidence_summary=(
                        f"Photo region '{photo_reg.name}' evaluated. Signals: {', '.join(reg_signals) if reg_signals else 'none'}."
                    ),
                )
            )

        avg_confidence = round(total_confidence / len(regions.photo), 2) if regions.photo else 0.8
        photo_replacement_suspected = bool(
            ("photo_occlusion_or_blackout" in aggregated_signals)
            or (len(aggregated_signals) >= 2)
            or (highest_score >= 50.0)
        )
        suspected = (highest_score >= 50.0) or (len(aggregated_signals) >= 2)

        result = PhotoAnalysisResult(
            enabled=True,
            regions_analyzed=len(regions.photo),
            photo_replacement_suspected=photo_replacement_suspected,
            score=round(highest_score, 1),
            confidence=avg_confidence,
            signals=aggregated_signals,
            region_results=region_details,
            reason=None,
        )

        return result, evidence, warnings
