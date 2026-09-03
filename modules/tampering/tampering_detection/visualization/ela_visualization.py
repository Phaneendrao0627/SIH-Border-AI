"""Error Level Analysis (ELA) heatmap and overlay visualization generator."""

from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np

from tampering_detection.config import DetectionConfig
from tampering_detection.io.image_loader import LoadedImage
from tampering_detection.logging_config import get_logger

logger = get_logger("visualization.ela")


def generate_ela_artifacts(
    image: LoadedImage,
    ela_gray: np.ndarray,
    config: DetectionConfig,
    output_dir: Optional[str] = None,
    document_id: Optional[str] = None,
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Generate colorized ELA difference heatmap and alpha-blended overlay.

    Args:
        image: LoadedImage containing RGB document.
        ela_gray: 2D numpy array of ELA absolute differences.
        config: Central configuration for scale factor and privacy.
        output_dir: Target output directory for artifact images.
        document_id: Optional identifier for file naming.

    Returns:
        Tuple of (ela_map_path, ela_overlay_path, warning_message).
    """
    if not config.get_effective_save_artifacts():
        return None, None, None

    target_dir = Path(output_dir or "artifacts")
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        return None, None, f"Failed to create artifact directory {target_dir}: {e}"

    doc_tag = (document_id or "document").replace("/", "_").replace("\\", "_")

    # 1. Scale ELA gray map for visual perception
    scaled_gray = np.clip(ela_gray * config.ela_scale_factor, 0, 255).astype(np.uint8)

    # 2. Apply COLORMAP_JET to generate heatmap
    heatmap_bgr = cv2.applyColorMap(scaled_gray, cv2.COLORMAP_JET)

    # 3. Alpha blend heatmap over original image
    orig_bgr = image.bgr_array
    overlay_bgr = cv2.addWeighted(orig_bgr, 0.60, heatmap_bgr, 0.40, 0)

    # 4. Save to disk safely
    ela_map_path = str(target_dir / f"{doc_tag}_ela_heatmap.jpg")
    overlay_path = str(target_dir / f"{doc_tag}_ela_overlay.jpg")

    try:
        cv2.imwrite(ela_map_path, heatmap_bgr, [cv2.IMWRITE_JPEG_QUALITY, 92])
        cv2.imwrite(overlay_path, overlay_bgr, [cv2.IMWRITE_JPEG_QUALITY, 92])
        return ela_map_path, overlay_path, None
    except Exception as e:
        logger.error("Failed to write ELA visual artifacts: %s", e)
        return None, None, f"Artifact generation failed: {e}"
