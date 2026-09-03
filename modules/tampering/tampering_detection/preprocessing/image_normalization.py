"""Image normalization and safe geometric cropping utilities."""

from typing import Optional, Tuple
import numpy as np

from tampering_detection.schemas import RegionCoordinate


def safe_crop_region(
    image_array: np.ndarray,
    region: RegionCoordinate,
) -> np.ndarray:
    """Safely extract a rectangular crop from an image array with bounds validation.

    Args:
        image_array: 2D or 3D NumPy array representing the image.
        region: RegionCoordinate specification.

    Returns:
        Sub-array crop of the specified region.
    """
    h, w = image_array.shape[:2]
    x1 = max(0, min(region.x, w - 1))
    y1 = max(0, min(region.y, h - 1))
    x2 = max(x1 + 1, min(region.x + region.width, w))
    y2 = max(y1 + 1, min(region.y + region.height, h))

    return image_array[y1:y2, x1:x2].copy()


def extract_border_strips(
    image_array: np.ndarray,
    region: RegionCoordinate,
    strip_width: int = 6,
) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
    """Extract inner and outer boundary strips for boundary discontinuity analysis.

    Args:
        image_array: 2D or 3D image array.
        region: RegionCoordinate bounding box.
        strip_width: Width of the perimeter strip in pixels.

    Returns:
        Tuple of (inner_strip_pixels, outer_strip_pixels) or (None, None) if context is insufficient.
    """
    h, w = image_array.shape[:2]
    x, y, rw, rh = region.x, region.y, region.width, region.height

    # Outer bounding box expanded by strip_width
    out_x1 = max(0, x - strip_width)
    out_y1 = max(0, y - strip_width)
    out_x2 = min(w, x + rw + strip_width)
    out_y2 = min(h, y + rh + strip_width)

    # Inner bounding box contracted by strip_width
    in_x1 = min(x + rw - 1, x + strip_width)
    in_y1 = min(y + rh - 1, y + strip_width)
    in_x2 = max(x, x + rw - strip_width)
    in_y2 = max(y, y + rh - strip_width)

    if in_x2 <= in_x1 or in_y2 <= in_y1:
        return None, None

    # Masks
    mask_outer = np.zeros((h, w), dtype=bool)
    mask_outer[out_y1:out_y2, out_x1:out_x2] = True
    mask_outer[y : y + rh, x : x + rw] = False

    mask_inner = np.zeros((h, w), dtype=bool)
    mask_inner[y : y + rh, x : x + rw] = True
    mask_inner[in_y1:in_y2, in_x1:in_x2] = False

    outer_pixels = image_array[mask_outer]
    inner_pixels = image_array[mask_inner]

    if len(outer_pixels) < 20 or len(inner_pixels) < 20:
        return None, None

    return inner_pixels, outer_pixels


def extract_surrounding_background(
    image_array: np.ndarray,
    region: RegionCoordinate,
    ring_thickness: int = 25,
) -> Optional[np.ndarray]:
    """Extract a background ring immediately surrounding a region.

    Args:
        image_array: 2D or 3D image array.
        region: RegionCoordinate bounding box.
        ring_thickness: Thickness of the outer surrounding ring in pixels.

    Returns:
        Array of surrounding background pixels, or None if insufficient boundary.
    """
    h, w = image_array.shape[:2]
    x, y, rw, rh = region.x, region.y, region.width, region.height

    out_x1 = max(0, x - ring_thickness)
    out_y1 = max(0, y - ring_thickness)
    out_x2 = min(w, x + rw + ring_thickness)
    out_y2 = min(h, y + rh + ring_thickness)

    mask = np.zeros((h, w), dtype=bool)
    mask[out_y1:out_y2, out_x1:out_x2] = True
    mask[y : y + rh, x : x + rw] = False

    surrounding_pixels = image_array[mask]
    if len(surrounding_pixels) < 50:
        return None

    return surrounding_pixels
