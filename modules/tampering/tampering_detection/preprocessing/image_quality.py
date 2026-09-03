"""Image quality assessment assessing sharpness, resolution, exposure, and contrast."""

import cv2
import numpy as np

from tampering_detection.config import DetectionConfig
from tampering_detection.io.image_loader import LoadedImage
from tampering_detection.logging_config import get_logger
from tampering_detection.schemas import ImageQualityMetrics

logger = get_logger("preprocessing.image_quality")


def assess_image_quality(image: LoadedImage, config: DetectionConfig) -> ImageQualityMetrics:
    """Measure document image quality metrics.

    Calculates:
    - Width, height, channels
    - Blur metric using variance of Laplacian
    - Low-resolution detection
    - Overexposure and underexposure ratios
    - Grayscale contrast standard deviation
    - Detected color mode

    Note: Poor image quality reduces forensic confidence rather than increasing fraud score.

    Args:
        image: Normalized LoadedImage instance.
        config: Central configuration containing quality thresholds.

    Returns:
        ImageQualityMetrics schema instance.
    """
    gray = image.gray_array
    h, w = gray.shape

    # 1. Blur calculation via Laplacian variance
    try:
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        blur_score = float(laplacian.var())
    except Exception as e:
        logger.warning("Error calculating Laplacian variance: %s", e)
        blur_score = 0.0

    # 2. Low-resolution heuristic
    low_res = bool(
        w < config.min_width
        or h < config.min_height
        or (w * h < 300_000)
    )

    # 3. Exposure analysis
    total_pixels = float(h * w) if (h * w) > 0 else 1.0
    overexposed_pixels = np.count_nonzero(gray >= 250)
    underexposed_pixels = np.count_nonzero(gray <= 10)

    overexposed_ratio = overexposed_pixels / total_pixels
    underexposed_ratio = underexposed_pixels / total_pixels

    is_overexposed = bool(overexposed_ratio > config.exposure_outlier_ratio)
    is_underexposed = bool(underexposed_ratio > config.exposure_outlier_ratio)

    # 4. Contrast score (standard deviation of pixel intensities)
    contrast_score = float(np.std(gray))

    # 5. Color mode identification
    if image.original_channels == 1 or image.original_mode in ("L", "1"):
        color_mode = "Grayscale"
    elif image.original_channels == 4 or image.original_mode == "RGBA":
        color_mode = "RGBA"
    else:
        color_mode = "RGB"

    return ImageQualityMetrics(
        width=w,
        height=h,
        channels=image.original_channels,
        blur_score=round(blur_score, 2),
        low_resolution=low_res,
        is_overexposed=is_overexposed,
        is_underexposed=is_underexposed,
        contrast_score=round(contrast_score, 2),
        color_mode=color_mode,
        was_resized=image.was_resized,
    )
