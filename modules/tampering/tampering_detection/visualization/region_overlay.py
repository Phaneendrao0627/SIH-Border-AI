"""Region bounding-box overlay visualization generator."""

from pathlib import Path
from typing import List, Optional, Tuple

import cv2

from tampering_detection.config import DetectionConfig
from tampering_detection.io.image_loader import LoadedImage
from tampering_detection.logging_config import get_logger
from tampering_detection.schemas import DocumentRegions, RegionForensicDetail

logger = get_logger("visualization.region_overlay")


def generate_region_overlay(
    image: LoadedImage,
    regions: DocumentRegions,
    region_details: List[RegionForensicDetail],
    config: DetectionConfig,
    output_dir: Optional[str] = None,
    document_id: Optional[str] = None,
) -> Tuple[Optional[str], Optional[str]]:
    """Draw color-coded bounding boxes and forensic labels on document image.

    Args:
        image: LoadedImage containing document array.
        regions: Validated DocumentRegions.
        region_details: Forensic evaluations for each region.
        config: Central configuration.
        output_dir: Target output directory.
        document_id: Optional document identifier.

    Returns:
        Tuple of (saved_overlay_path, warning_message).
    """
    if not config.get_effective_save_artifacts():
        return None, None

    all_regions = regions.photo + regions.text + regions.stamp
    if not all_regions:
        return None, None

    target_dir = Path(output_dir or "artifacts")
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        return None, f"Failed to create artifact directory {target_dir}: {e}"

    doc_tag = (document_id or "document").replace("/", "_").replace("\\", "_")
    annotated = image.bgr_array.copy()

    # Map details by region name
    details_map = {d.region_name: d for d in region_details}

    for reg in all_regions:
        detail = details_map.get(reg.name)
        score = detail.tampering_score if detail else 0.0

        # Choose color based on score (BGR format)
        if score >= 60.0:
            color = (0, 0, 220)       # Red: High suspicion
        elif score >= 30.0:
            color = (0, 165, 255)     # Orange: Medium suspicion
        else:
            color = (0, 200, 0)       # Green: Low suspicion

        # Draw bounding box
        x, y, w, h = reg.x, reg.y, reg.width, reg.height
        cv2.rectangle(annotated, (x, y), (x + w, y + h), color, 2)

        # Label banner
        label = f"{reg.name} ({int(score)})"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.45
        thickness = 1
        (text_w, text_h), baseline = cv2.getTextSize(label, font, font_scale, thickness)

        label_y = max(y - 6, text_h + 4)
        cv2.rectangle(
            annotated,
            (x, label_y - text_h - 4),
            (x + text_w + 6, label_y + baseline),
            color,
            -1,
        )
        cv2.putText(
            annotated,
            label,
            (x + 3, label_y - 2),
            font,
            font_scale,
            (255, 255, 255),
            thickness,
            cv2.LINE_AA,
        )

    out_path = str(target_dir / f"{doc_tag}_regions_overlay.jpg")
    try:
        cv2.imwrite(out_path, annotated, [cv2.IMWRITE_JPEG_QUALITY, 90])
        return out_path, None
    except Exception as e:
        logger.error("Failed to write region overlay artifact: %s", e)
        return None, f"Failed to save region overlay: {e}"
