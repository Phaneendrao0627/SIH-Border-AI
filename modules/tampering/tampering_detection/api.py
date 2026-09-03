"""Public API entrypoint for Module 3: Tampering Detection."""

import time
from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Optional, Union

import numpy as np
from PIL import Image

from tampering_detection.config import DetectionConfig
from tampering_detection.detectors.ela_detector import ElaDetector
from tampering_detection.detectors.metadata_detector import MetadataDetector
from tampering_detection.detectors.photo_detector import PhotoDetector
from tampering_detection.detectors.stamp_detector import StampDetector
from tampering_detection.detectors.text_detector import TextDetector
from tampering_detection.exceptions import TamperingDetectionError
from tampering_detection.io.image_loader import load_image
from tampering_detection.logging_config import get_logger
from tampering_detection.preprocessing.image_quality import assess_image_quality
from tampering_detection.preprocessing.region_validation import validate_and_clamp_regions
from tampering_detection.schemas import (
    ArtifactsResult,
    DocumentRegions,
    PhotoAnalysisResult,
    ProcessingInfo,
    RegionForensicDetail,
    StampAnalysisResult,
    TamperingAnalysisSummary,
    TamperingDetectionResult,
    TextAnalysisResult,
)
from tampering_detection.scoring.confidence_estimator import estimate_confidence
from tampering_detection.scoring.score_aggregator import aggregate_scores
from tampering_detection.visualization.ela_visualization import generate_ela_artifacts
from tampering_detection.visualization.region_overlay import generate_region_overlay

logger = get_logger("api")


def analyze_document(
    image_source: Union[str, Path, bytes, BinaryIO, Image.Image, np.ndarray],
    document_id: Optional[str] = None,
    document_type: str = "unknown",
    regions: Optional[Union[Dict[str, Any], DocumentRegions]] = None,
    options: Optional[Union[Dict[str, Any], DetectionConfig]] = None,
) -> TamperingDetectionResult:
    """Analyze a document image for forensic signs of digital or physical alteration.

    Evaluates:
    - Image quality, clarity, and dimensions
    - EXIF metadata and software editing traces
    - Error Level Analysis (ELA) compression anomalies
    - Portrait photo replacement / boundary / noise mismatch
    - Text manipulation / stroke consistency / density
    - Stamp forgery / texture / duplicated visual pattern cloning

    Args:
        image_source: Path, bytes, file-like, PIL Image, or NumPy array.
        document_id: Optional opaque identifier for the document.
        document_type: Document category (e.g., 'passport', 'visa', 'id_card').
        regions: Optional dictionary or DocumentRegions with photo, text, stamp coordinates.
        options: Optional DetectionConfig or dictionary of configuration overrides.

    Returns:
        TamperingDetectionResult schema model containing score, risk level, confidence,
        detailed sub-analyses, explainable evidence items, and warnings.
    """
    start_time = time.perf_counter()

    # 1. Parse configuration
    if isinstance(options, DetectionConfig):
        cfg = options
    elif isinstance(options, dict):
        cfg = DetectionConfig(**options)
    else:
        cfg = DetectionConfig()

    # 2. Ingest and normalize image
    loaded_img = load_image(image_source, config=cfg, source_identifier=document_id)

    # 3. Assess image quality
    quality_metrics = assess_image_quality(loaded_img, cfg)

    # 4. Validate and clamp region coordinates
    validated_regions, region_warnings = validate_and_clamp_regions(
        regions, loaded_img.width, loaded_img.height
    )

    all_warnings: List[str] = list(region_warnings)
    all_flags: List[str] = []
    all_evidence = []
    all_region_details: List[RegionForensicDetail] = []
    detectors_run: List[str] = []
    detectors_skipped: List[str] = []
    detector_scores: Dict[str, Optional[float]] = {}

    # Mandatory baseline advisory warning
    all_warnings.append("This module provides forensic indicators only and requires human review.")

    # 5. Metadata Analysis
    meta_detector = MetadataDetector()
    meta_res, meta_evidence, meta_warnings = meta_detector.run(
        loaded_img, validated_regions, cfg
    )
    detectors_run.append("metadata")
    detector_scores["metadata"] = meta_res.score
    all_flags.extend(meta_res.flags)
    all_evidence.extend(meta_evidence)
    all_warnings.extend(meta_warnings)

    # 6. Error Level Analysis (ELA)
    ela_detector = ElaDetector()
    ela_res, ela_evidence, ela_warnings, ela_ctx = ela_detector.run(
        loaded_img, validated_regions, cfg
    )
    detectors_run.append("ela")
    detector_scores["ela"] = ela_res.score
    all_evidence.extend(ela_evidence)
    all_warnings.extend(ela_warnings)
    if ela_res.anomaly_regions:
        all_flags.append("ela_compression_anomaly_detected")

    # 7. Photo Replacement Analysis
    photo_detector = PhotoDetector()
    try:
        photo_res, photo_evidence, photo_warnings = photo_detector.run(
            loaded_img, validated_regions, cfg, context=ela_ctx
        )
        if photo_res.enabled:
            detectors_run.append("photo")
            detector_scores["photo"] = photo_res.score
            all_evidence.extend(photo_evidence)
            all_warnings.extend(photo_warnings)
            all_region_details.extend(photo_res.region_results)
            if photo_res.photo_replacement_suspected:
                all_flags.append("photo_replacement_suspected")
            for sig in photo_res.signals:
                flag_name = f"photo_{sig}"
                if flag_name not in all_flags:
                    all_flags.append(flag_name)
        else:
            detectors_skipped.append("photo")
            detector_scores["photo"] = None
    except Exception as e:
        logger.error("PhotoDetector failed unexpectedly: %s", e)
        all_warnings.append(f"INTERNAL_DETECTOR_ERROR: Photo detector error: {e}")
        detectors_skipped.append("photo")
        detector_scores["photo"] = None
        photo_res = PhotoAnalysisResult(
            enabled=False,
            regions_analyzed=0,
            photo_replacement_suspected=False,
            score=None,
            confidence=None,
            signals=[],
            region_results=[],
            reason=f"Detector failed: {e}",
        )

    # 8. Text Manipulation Analysis
    text_detector = TextDetector()
    try:
        text_res, text_evidence, text_warnings = text_detector.run(
            loaded_img, validated_regions, cfg, context=ela_ctx
        )
        if text_res.enabled:
            detectors_run.append("text")
            detector_scores["text"] = text_res.score
            all_evidence.extend(text_evidence)
            all_warnings.extend(text_warnings)
            all_region_details.extend(text_res.region_results)
            if text_res.text_manipulation_suspected:
                all_flags.append("text_manipulation_suspected")
            for sig in text_res.signals:
                flag_name = f"text_{sig}"
                if flag_name not in all_flags:
                    all_flags.append(flag_name)
        else:
            detectors_skipped.append("text")
            detector_scores["text"] = None
    except Exception as e:
        logger.error("TextDetector failed unexpectedly: %s", e)
        all_warnings.append(f"INTERNAL_DETECTOR_ERROR: Text detector error: {e}")
        detectors_skipped.append("text")
        detector_scores["text"] = None
        text_res = TextAnalysisResult(
            enabled=False,
            regions_analyzed=0,
            text_manipulation_suspected=False,
            score=None,
            confidence=None,
            signals=[],
            region_results=[],
            reason=f"Detector failed: {e}",
        )

    # 9. Stamp Forgery & Duplicate Analysis
    stamp_detector = StampDetector()
    try:
        stamp_res, stamp_evidence, stamp_warnings = stamp_detector.run(
            loaded_img, validated_regions, cfg, context=ela_ctx
        )
        if stamp_res.enabled:
            detectors_run.append("stamp")
            detector_scores["stamp"] = stamp_res.score
            all_evidence.extend(stamp_evidence)
            all_warnings.extend(stamp_warnings)
            all_region_details.extend(stamp_res.region_results)
            if stamp_res.stamp_forgery_suspected:
                all_flags.append("stamp_forgery_suspected")
            for sig in stamp_res.signals:
                flag_name = f"stamp_{sig}"
                if flag_name not in all_flags:
                    all_flags.append(flag_name)
        else:
            detectors_skipped.append("stamp")
            detector_scores["stamp"] = None
    except Exception as e:
        logger.error("StampDetector failed unexpectedly: %s", e)
        all_warnings.append(f"INTERNAL_DETECTOR_ERROR: Stamp detector error: {e}")
        detectors_skipped.append("stamp")
        detector_scores["stamp"] = None
        stamp_res = StampAnalysisResult(
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
            reason=f"Detector failed: {e}",
        )

    # 10. Aggregated Tampering Score and Risk Classification
    tampering_score, risk_level = aggregate_scores(
        detector_scores=detector_scores,
        evidence=all_evidence,
        config=cfg,
    )

    # 11. Holistic Confidence Estimation
    confidence = estimate_confidence(
        quality=quality_metrics,
        detectors_run=detectors_run,
        detectors_skipped=detectors_skipped,
        evidence=all_evidence,
        detector_scores=detector_scores,
        config=cfg,
        warnings=all_warnings,
    )

    # 12. Optional Visual Artifact Generation
    artifacts_res = ArtifactsResult()
    if cfg.get_effective_save_artifacts():
        ela_map_p, ela_over_p, ela_art_warn = generate_ela_artifacts(
            loaded_img, ela_ctx["ela_gray"], cfg, output_dir=cfg.artifacts_dir, document_id=document_id
        )
        if ela_art_warn:
            all_warnings.append(ela_art_warn)
        artifacts_res.ela_map = ela_map_p
        artifacts_res.ela_overlay = ela_over_p

        reg_over_p, reg_art_warn = generate_region_overlay(
            loaded_img, validated_regions, all_region_details, cfg, output_dir=cfg.artifacts_dir, document_id=document_id
        )
        if reg_art_warn:
            all_warnings.append(reg_art_warn)
        if reg_over_p:
            artifacts_res.region_visualizations.append(reg_over_p)

    # 13. Assemble Final Structured Result
    elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

    summary = TamperingAnalysisSummary(
        metadata=meta_res,
        ela=ela_res,
        photo_analysis=photo_res,
        text_analysis=text_res,
        stamp_analysis=stamp_res,
    )

    processing_info = ProcessingInfo(
        elapsed_ms=elapsed_ms,
        detectors_run=detectors_run,
        detectors_skipped=detectors_skipped,
    )

    # Deduplicate flags while preserving order
    unique_flags = list(dict.fromkeys(all_flags))

    return TamperingDetectionResult(
        schema_version="1.0",
        document_id=document_id,
        document_type=document_type,
        status="completed",
        tampering_score=tampering_score,
        risk_level=risk_level,
        confidence=confidence,
        tampering_analysis=summary,
        flags=unique_flags,
        evidence=all_evidence,
        warnings=all_warnings,
        quality=quality_metrics,
        artifacts=artifacts_res,
        processing=processing_info,
    )
