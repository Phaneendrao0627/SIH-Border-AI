"""Image loading and normalization module supporting diverse input representations."""

import io
from pathlib import Path
from typing import BinaryIO, Optional, Tuple, Union

import cv2
import numpy as np
from PIL import Image

from tampering_detection.config import DetectionConfig
from tampering_detection.exceptions import (
    ImageFormatError,
    ImageLoadError,
    ImageSizeError,
)
from tampering_detection.logging_config import get_logger

logger = get_logger("io.image_loader")


class LoadedImage:
    """Encapsulates loaded image representations and properties."""

    def __init__(
        self,
        pil_image: Image.Image,
        rgb_array: np.ndarray,
        bgr_array: np.ndarray,
        gray_array: np.ndarray,
        original_format: str,
        original_mode: str,
        original_channels: int,
        raw_bytes: Optional[bytes] = None,
        source_identifier: Optional[str] = None,
        was_resized: bool = False,
    ):
        self.pil_image = pil_image
        self.rgb_array = rgb_array
        self.bgr_array = bgr_array
        self.gray_array = gray_array
        self.original_format = original_format
        self.original_mode = original_mode
        self.original_channels = original_channels
        self.raw_bytes = raw_bytes
        self.source_identifier = source_identifier
        self.was_resized = was_resized

    @property
    def width(self) -> int:
        return self.rgb_array.shape[1]

    @property
    def height(self) -> int:
        return self.rgb_array.shape[0]

    @property
    def shape(self) -> Tuple[int, int, int]:
        return self.rgb_array.shape


def load_image(
    image_source: Union[str, Path, bytes, BinaryIO, Image.Image, np.ndarray],
    config: Optional[DetectionConfig] = None,
    source_identifier: Optional[str] = None,
) -> LoadedImage:
    """Load and normalize an image from multiple possible sources.

    Supports:
    - Local file path (str or Path)
    - Raw bytes
    - File-like object (io.BytesIO)
    - PIL Image
    - NumPy array (2D grayscale or 3D BGR/RGB)

    Args:
        image_source: Input data source.
        config: Optional configuration for dimension boundaries.
        source_identifier: Optional opaque label (e.g. filename) for logging.

    Returns:
        LoadedImage with synchronized PIL and NumPy representations.

    Raises:
        ImageLoadError: If data is empty, missing, or unreadable.
        ImageFormatError: If format is corrupted or unsupported.
        ImageSizeError: If dimensions exceed max_dimension or are below min limits.
    """
    cfg = config or DetectionConfig()
    raw_bytes: Optional[bytes] = None
    pil_img: Optional[Image.Image] = None
    original_format = "UNKNOWN"
    original_mode = "RGB"

    # 1. Path input
    if isinstance(image_source, (str, Path)):
        path = Path(image_source)
        if not path.exists() or not path.is_file():
            raise ImageLoadError(f"Image file not found: {path}", error_code="IMAGE_NOT_FOUND")
        try:
            raw_bytes = path.read_bytes()
            if len(raw_bytes) == 0:
                raise ImageLoadError(f"Image file is empty: {path}", error_code="IMAGE_UNREADABLE")
            pil_img = Image.open(io.BytesIO(raw_bytes))
            original_format = pil_img.format or path.suffix.lstrip(".").upper() or "UNKNOWN"
            original_mode = pil_img.mode
            if not source_identifier:
                source_identifier = path.name
        except Exception as e:
            if isinstance(e, ImageLoadError):
                raise
            raise ImageLoadError(f"Failed to read image from {path}: {e}", error_code="IMAGE_UNREADABLE") from e

    # 2. Bytes input
    elif isinstance(image_source, bytes):
        if len(image_source) == 0:
            raise ImageLoadError("Empty byte array provided for image source", error_code="IMAGE_UNREADABLE")
        raw_bytes = image_source
        try:
            pil_img = Image.open(io.BytesIO(raw_bytes))
            original_format = pil_img.format or "UNKNOWN"
            original_mode = pil_img.mode
        except Exception as e:
            raise ImageFormatError(f"Failed to parse image from bytes: {e}", error_code="IMAGE_UNREADABLE") from e

    # 3. File-like object
    elif hasattr(image_source, "read"):
        try:
            raw_bytes = image_source.read()
            if len(raw_bytes) == 0:
                raise ImageLoadError("File-like image source is empty", error_code="IMAGE_UNREADABLE")
            pil_img = Image.open(io.BytesIO(raw_bytes))
            original_format = pil_img.format or "UNKNOWN"
            original_mode = pil_img.mode
        except Exception as e:
            if isinstance(e, ImageLoadError):
                raise
            raise ImageLoadError(f"Failed to read from file-like object: {e}", error_code="IMAGE_UNREADABLE") from e

    # 4. PIL Image
    elif isinstance(image_source, Image.Image):
        pil_img = image_source.copy()
        original_format = pil_img.format or "PIL"
        original_mode = pil_img.mode
        try:
            buf = io.BytesIO()
            fmt = "PNG" if original_mode == "RGBA" else "JPEG"
            pil_img.save(buf, format=fmt)
            raw_bytes = buf.getvalue()
        except Exception:
            raw_bytes = None

    # 5. NumPy Array
    elif isinstance(image_source, np.ndarray):
        arr = image_source.copy()
        if arr.size == 0:
            raise ImageLoadError("NumPy array is empty", error_code="IMAGE_UNREADABLE")

        original_format = "NUMPY"
        if arr.ndim == 2:
            original_mode = "L"
            original_channels = 1
            gray_array = arr.astype(np.uint8)
            rgb_array = cv2.cvtColor(gray_array, cv2.COLOR_GRAY2RGB)
            bgr_array = cv2.cvtColor(gray_array, cv2.COLOR_GRAY2BGR)
            pil_img = Image.fromarray(rgb_array)
        elif arr.ndim == 3:
            original_channels = arr.shape[2]
            if original_channels == 1:
                original_mode = "L"
                gray_array = arr[:, :, 0].astype(np.uint8)
                rgb_array = cv2.cvtColor(gray_array, cv2.COLOR_GRAY2RGB)
                bgr_array = cv2.cvtColor(gray_array, cv2.COLOR_GRAY2BGR)
                pil_img = Image.fromarray(rgb_array)
            elif original_channels == 3:
                # Default convention: assume RGB for arrays passed to PIL or standard libraries
                original_mode = "RGB"
                rgb_array = arr.astype(np.uint8)
                bgr_array = cv2.cvtColor(rgb_array, cv2.COLOR_RGB2BGR)
                gray_array = cv2.cvtColor(rgb_array, cv2.COLOR_RGB2GRAY)
                pil_img = Image.fromarray(rgb_array)
            elif original_channels == 4:
                original_mode = "RGBA"
                rgba_array = arr.astype(np.uint8)
                rgb_array = cv2.cvtColor(rgba_array, cv2.COLOR_RGBA2RGB)
                bgr_array = cv2.cvtColor(rgba_array, cv2.COLOR_RGBA2BGR)
                gray_array = cv2.cvtColor(rgb_array, cv2.COLOR_RGB2GRAY)
                pil_img = Image.fromarray(rgb_array)
            else:
                raise ImageFormatError(f"Unsupported channel count: {original_channels}", error_code="UNSUPPORTED_CHANNELS")
        else:
            raise ImageFormatError(f"Unsupported array dimensions: {arr.ndim}", error_code="UNSUPPORTED_DIMENSIONS")

        # Encode bytes if needed for metadata extractors
        try:
            buf = io.BytesIO()
            pil_img.save(buf, format="PNG")
            raw_bytes = buf.getvalue()
        except Exception:
            raw_bytes = None

        rgb_pil = pil_img
        if not source_identifier:
            source_identifier = "numpy_array"

    else:
        raise ImageLoadError(
            f"Unsupported image_source type: {type(image_source).__name__}",
            error_code="UNSUPPORTED_IMAGE_SOURCE",
        )

    # Process PIL image obtained from path, bytes, or file-like object
    if pil_img is None:
        raise ImageLoadError("Failed to obtain a valid PIL Image", error_code="IMAGE_UNREADABLE")

    # Determine channel count from original PIL mode
    if original_mode == "RGBA":
        original_channels = 4
    elif original_mode in ("L", "1"):
        original_channels = 1
    elif original_mode == "CMYK":
        original_channels = 4
    else:
        original_channels = 3

    # Ensure RGB conversion for analysis
    rgb_pil = pil_img.convert("RGB")
    rgb_array = np.array(rgb_pil, dtype=np.uint8)
    bgr_array = cv2.cvtColor(rgb_array, cv2.COLOR_RGB2BGR)
    gray_array = cv2.cvtColor(rgb_array, cv2.COLOR_RGB2GRAY)

    h, w = rgb_array.shape[:2]

    # Validate image dimensions
    if w < 10 or h < 10:
        raise ImageSizeError(
            f"Image dimensions ({w}x{h}) are too small for forensic evaluation",
            error_code="IMAGE_TOO_SMALL",
        )

    if w > cfg.max_dimension or h > cfg.max_dimension:
        raise ImageSizeError(
            f"Image dimensions ({w}x{h}) exceed maximum supported dimension ({cfg.max_dimension})",
            error_code="IMAGE_TOO_LARGE",
        )

    return LoadedImage(
        pil_image=rgb_pil,
        rgb_array=rgb_array,
        bgr_array=bgr_array,
        gray_array=gray_array,
        original_format=original_format,
        original_mode=original_mode,
        original_channels=original_channels,
        raw_bytes=raw_bytes,
        source_identifier=source_identifier,
        was_resized=False,
    )
