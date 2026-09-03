import io
import logging
from typing import Any, Dict, List, Optional, Tuple

import exifread
from PIL import ExifTags, Image

from tampering_detection.logging_config import get_logger

logger = get_logger("io.metadata_reader")
# Suppress benign third-party warnings from exifread for formats/files without EXIF (e.g., PNG)
logging.getLogger("exifread").setLevel(logging.ERROR)

# Safe tags allowed to be exposed in the output without privacy risk
SAFE_METADATA_KEYS = {
    "Image Make",
    "Image Model",
    "Image Software",
    "Image ProcessingSoftware",
    "Image DateTime",
    "EXIF DateTimeOriginal",
    "EXIF DateTimeDigitized",
    "EXIF ExifImageWidth",
    "EXIF ExifImageLength",
    "EXIF Compression",
    "Image Orientation",
    "Software",
    "ProcessingSoftware",
    "Make",
    "Model",
    "DateTime",
    "DateTimeOriginal",
    "DateTimeDigitized",
    "Orientation",
}

# Explicitly disallowed tags that might contain sensitive personal location or biometric data
DISALLOWED_TAG_SUBSTRINGS = ["gps", "serial", "owner", "author", "copyright", "usercomment"]


def _is_safe_tag(tag_name: str) -> bool:
    """Check whether an EXIF tag is safe from a privacy perspective."""
    lower_tag = tag_name.lower()
    for forbidden in DISALLOWED_TAG_SUBSTRINGS:
        if forbidden in lower_tag:
            return False
    return True


def _sanitize_value(val: Any) -> Any:
    """Recursively convert EXIF values into standard JSON-serializable types."""
    if isinstance(val, (int, float, bool, str)):
        return val
    if hasattr(val, "printable"):
        return str(val.printable)
    if hasattr(val, "values"):
        if isinstance(val.values, list):
            return [_sanitize_value(v) for v in val.values[:10]]
        return str(val.values)
    return str(val)


def extract_metadata(
    raw_bytes: Optional[bytes],
    pil_image: Optional[Image.Image] = None,
) -> Tuple[bool, Dict[str, Any], Dict[str, Optional[str]], List[str]]:
    """Extract and sanitize EXIF metadata from raw image bytes or PIL Image.

    Args:
        raw_bytes: Optional binary image data.
        pil_image: Optional PIL Image object.

    Returns:
        Tuple of:
        - available: bool (whether any valid metadata was retrieved)
        - safe_tags: Dict[str, Any] (sanitized key-value tags)
        - timestamps: Dict[str, Optional[str]] (extracted datetime strings)
        - warnings: List[str] (any non-fatal warnings encountered)
    """
    safe_tags: Dict[str, Any] = {}
    timestamps: Dict[str, Optional[str]] = {
        "DateTime": None,
        "DateTimeOriginal": None,
        "DateTimeDigitized": None,
        "ModifyDate": None,
    }
    warnings: List[str] = []
    metadata_found = False

    # 1. Primary extraction using exifread on raw bytes
    if raw_bytes and len(raw_bytes) > 0:
        try:
            tags = exifread.process_file(io.BytesIO(raw_bytes), details=False)
            if tags:
                metadata_found = True
                for k, v in tags.items():
                    if _is_safe_tag(k):
                        sanitized = _sanitize_value(v)
                        safe_tags[k] = sanitized

                        # Track timestamps
                        if "datetimeoriginal" in k.lower():
                            timestamps["DateTimeOriginal"] = str(sanitized)
                        elif "datetimedigitized" in k.lower():
                            timestamps["DateTimeDigitized"] = str(sanitized)
                        elif "datetime" in k.lower() and "original" not in k.lower():
                            timestamps["DateTime"] = str(sanitized)
                        elif "modify" in k.lower():
                            timestamps["ModifyDate"] = str(sanitized)
        except Exception as e:
            logger.debug("exifread parsing error: %s", e)
            warnings.append(f"Primary EXIF parser encountered an issue: {str(e)[:100]}")

    # 2. Secondary fallback using PIL ExifTags if available and safe_tags is empty
    if not safe_tags and pil_image is not None:
        try:
            exif_data = pil_image.getexif()
            if exif_data and len(exif_data) > 0:
                metadata_found = True
                for tag_id, value in exif_data.items():
                    tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
                    if _is_safe_tag(tag_name):
                        sanitized = _sanitize_value(value)
                        safe_tags[tag_name] = sanitized

                        if tag_name in ("DateTimeOriginal", "DateTimeDigitized", "DateTime"):
                            timestamps[tag_name] = str(sanitized)
        except Exception as e:
            logger.debug("PIL getexif error: %s", e)

    # 3. Check for Pillow info dictionary entries (e.g. software or comments in PNG)
    if pil_image and hasattr(pil_image, "info") and pil_image.info:
        for k, v in pil_image.info.items():
            if isinstance(k, str) and _is_safe_tag(k):
                if k.lower() in ("software", "processingsoftware", "comment", "description"):
                    safe_tags[k] = _sanitize_value(v)
                    metadata_found = True

    return metadata_found, safe_tags, timestamps, warnings
