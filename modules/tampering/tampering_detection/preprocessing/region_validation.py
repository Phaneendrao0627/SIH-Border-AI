"""Region validation and boundary clamping for document regions."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from tampering_detection.logging_config import get_logger
from tampering_detection.schemas import DocumentRegions, RegionCoordinate

logger = get_logger("preprocessing.region_validation")

MIN_PHOTO_WIDTH = 25
MIN_PHOTO_HEIGHT = 25
MIN_TEXT_WIDTH = 10
MIN_TEXT_HEIGHT = 5
MIN_STAMP_WIDTH = 20
MIN_STAMP_HEIGHT = 20


def validate_and_clamp_regions(
    raw_regions: Optional[Union[Dict[str, Any], DocumentRegions]],
    image_width: int,
    image_height: int,
) -> Tuple[DocumentRegions, List[str]]:
    """Validate, sanitize, and clamp region bounding boxes within image boundaries.

    Args:
        raw_regions: Input region dictionary, DocumentRegions model, or None.
        image_width: Target image width in pixels.
        image_height: Target image height in pixels.

    Returns:
        Tuple of:
        - Validated DocumentRegions object
        - List of warning messages generated during validation
    """
    warnings: List[str] = []
    validated_regions = DocumentRegions()

    if raw_regions is None:
        return validated_regions, warnings

    # Support file path strings or Path objects
    if isinstance(raw_regions, (str, Path)):
        try:
            with open(raw_regions, "r", encoding="utf-8") as f:
                regions_dict = json.load(f)
        except Exception as e:
            warnings.append(f"INVALID_REGION: Failed to load regions JSON from '{raw_regions}': {e}")
            return validated_regions, warnings
    # Convert DocumentRegions to dict if needed
    elif isinstance(raw_regions, DocumentRegions):
        regions_dict = raw_regions.model_dump()
    elif isinstance(raw_regions, dict):
        regions_dict = raw_regions
    else:
        warnings.append(f"INVALID_REGION: Expected dict, DocumentRegions, or file path, got {type(raw_regions).__name__}")
        return validated_regions, warnings

    def process_category(category_name: str, min_w: int, min_h: int) -> List[RegionCoordinate]:
        raw_list = regions_dict.get(category_name, [])
        if not isinstance(raw_list, list):
            warnings.append(f"INVALID_REGION: Category '{category_name}' must be a list of regions.")
            return []

        clean_list: List[RegionCoordinate] = []
        for idx, item in enumerate(raw_list):
            if not isinstance(item, dict):
                warnings.append(f"INVALID_REGION: Item {idx} in '{category_name}' is not an object.")
                continue

            name = str(item.get("name", f"{category_name}_{idx + 1}"))
            try:
                x = int(item.get("x", 0))
                y = int(item.get("y", 0))
                w = int(item.get("width", 0))
                h = int(item.get("height", 0))
            except (ValueError, TypeError):
                warnings.append(f"INVALID_REGION: Non-integer coordinates in region '{name}'.")
                continue

            if w <= 0 or h <= 0:
                warnings.append(f"INVALID_REGION: Non-positive dimensions ({w}x{h}) in region '{name}'.")
                continue

            # Check if completely outside bounds
            if x >= image_width or y >= image_height or (x + w) <= 0 or (y + h) <= 0:
                warnings.append(f"INVALID_REGION: Region '{name}' lies completely outside image boundaries.")
                continue

            # Clamping
            clamped_x = max(0, min(x, image_width - 1))
            clamped_y = max(0, min(y, image_height - 1))
            clamped_w = min(w, image_width - clamped_x)
            clamped_h = min(h, image_height - clamped_y)

            if (clamped_x != x) or (clamped_y != y) or (clamped_w != w) or (clamped_h != h):
                warnings.append(
                    f"Region '{name}' coordinates were clamped to image boundaries "
                    f"([{x}, {y}, {w}, {h}] -> [{clamped_x}, {clamped_y}, {clamped_w}, {clamped_h}])."
                )

            # Check minimum size constraints
            if clamped_w < min_w or clamped_h < min_h:
                warnings.append(
                    f"REGION_TOO_SMALL: Region '{name}' ({clamped_w}x{clamped_h}) is smaller than minimum "
                    f"allowed size ({min_w}x{min_h}) for category '{category_name}' and will be skipped."
                )
                continue

            clean_list.append(
                RegionCoordinate(
                    name=name,
                    x=clamped_x,
                    y=clamped_y,
                    width=clamped_w,
                    height=clamped_h,
                )
            )

        return clean_list

    validated_regions.photo = process_category("photo", MIN_PHOTO_WIDTH, MIN_PHOTO_HEIGHT)
    validated_regions.text = process_category("text", MIN_TEXT_WIDTH, MIN_TEXT_HEIGHT)
    validated_regions.stamp = process_category("stamp", MIN_STAMP_WIDTH, MIN_STAMP_HEIGHT)

    return validated_regions, warnings
