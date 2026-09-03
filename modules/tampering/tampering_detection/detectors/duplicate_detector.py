"""Duplicate visual pattern and copy-paste detector."""

from typing import Any, Dict, List, Optional, Tuple

import cv2
import imagehash
import numpy as np
from PIL import Image

from tampering_detection.config import DetectionConfig
from tampering_detection.io.image_loader import LoadedImage
from tampering_detection.logging_config import get_logger
from tampering_detection.schemas import RegionCoordinate

logger = get_logger("detectors.duplicate")


class DuplicateDetector:
    """Detects duplicated or cloned image patches using perceptual hashing and feature matching."""

    def __init__(self):
        self.name = "duplicate_analysis"

    def compare_regions_perceptual(
        self,
        img1_rgb: np.ndarray,
        img2_rgb: np.ndarray,
        hash_threshold: int = 5,
    ) -> Tuple[bool, int, float]:
        """Compare two image crops using perceptual hashing.

        Args:
            img1_rgb: First image patch (RGB).
            img2_rgb: Second image patch (RGB).
            hash_threshold: Maximum Hamming distance to consider suspicious duplicate.

        Returns:
            Tuple of (is_duplicate: bool, hamming_dist: int, similarity_ratio: float).
        """
        if img1_rgb.size < 40 or img2_rgb.size < 40:
            return False, 64, 0.0

        # Avoid comparing completely uniform/flat regions
        if np.std(img1_rgb) < 3.0 or np.std(img2_rgb) < 3.0:
            return False, 64, 0.0

        p1 = Image.fromarray(img1_rgb)
        p2 = Image.fromarray(img2_rgb)

        h1 = imagehash.phash(p1)
        h2 = imagehash.phash(p2)

        dist = h1 - h2
        similarity = max(0.0, 1.0 - (dist / 64.0))

        is_dup = bool(dist <= hash_threshold)
        return is_dup, dist, similarity

    def find_duplicate_in_document(
        self,
        target_crop_gray: np.ndarray,
        full_image_gray: np.ndarray,
        target_region: RegionCoordinate,
        match_threshold: float = 0.88,
    ) -> Tuple[bool, float, Optional[Tuple[int, int]]]:
        """Search full document for a duplicated instance of the target crop using normalized template matching.

        Args:
            target_crop_gray: Grayscale template crop.
            full_image_gray: Grayscale full document.
            target_region: Coordinates of the original region to mask out self-match.
            match_threshold: Cross-correlation score threshold.

        Returns:
            Tuple of (found_duplicate, max_score, location_xy).
        """
        th, tw = target_crop_gray.shape
        fh, fw = full_image_gray.shape

        if th >= fh or tw >= fw or th < 20 or tw < 20:
            return False, 0.0, None

        # Mask out target region and immediate neighborhood to prevent self-matching
        search_image = full_image_gray.copy()
        pad = 15
        mx1 = max(0, target_region.x - pad)
        my1 = max(0, target_region.y - pad)
        mx2 = min(fw, target_region.x + target_region.width + pad)
        my2 = min(fh, target_region.y + target_region.height + pad)
        search_image[my1:my2, mx1:mx2] = 0

        # Run template matching
        res = cv2.matchTemplate(search_image, target_crop_gray, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

        if max_val >= match_threshold:
            return True, float(max_val), max_loc

        return False, float(max_val), None
