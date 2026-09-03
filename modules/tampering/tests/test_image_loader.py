"""Unit tests for image loading, format normalization, and multi-channel handling."""

import io
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
import pytest

from tampering_detection.config import DetectionConfig
from tampering_detection.exceptions import (
    ImageFormatError,
    ImageLoadError,
    ImageSizeError,
)
from tampering_detection.io.image_loader import load_image


def test_jpeg_input(tmp_path):
    """Test 8: JPEG input from local disk path and bytes."""
    img_path = tmp_path / "test.jpg"
    arr = np.full((300, 400, 3), 200, dtype=np.uint8)
    cv2.imwrite(str(img_path), arr)

    # 1. From Path
    loaded = load_image(str(img_path))
    assert loaded.width == 400
    assert loaded.height == 300
    assert loaded.rgb_array.shape == (300, 400, 3)

    # 2. From Bytes
    loaded_bytes = load_image(img_path.read_bytes())
    assert loaded_bytes.width == 400
    assert loaded_bytes.height == 300


def test_png_input(tmp_path):
    """Test 9: PNG lossless format input."""
    img_path = tmp_path / "test.png"
    arr = np.full((300, 400, 3), 180, dtype=np.uint8)
    cv2.imwrite(str(img_path), arr)

    loaded = load_image(img_path)
    assert loaded.width == 400
    assert loaded.height == 300
    assert loaded.original_format == "PNG"


def test_grayscale_input():
    """Test 10: 2D Grayscale input array and PIL 'L' mode."""
    # 2D NumPy array
    gray_arr = np.full((280, 380), 128, dtype=np.uint8)
    loaded_arr = load_image(gray_arr)
    assert loaded_arr.width == 380
    assert loaded_arr.height == 280
    assert loaded_arr.original_channels == 1
    assert loaded_arr.rgb_array.shape == (280, 380, 3)

    # PIL 'L' image
    pil_gray = Image.fromarray(gray_arr, mode="L")
    loaded_pil = load_image(pil_gray)
    assert loaded_pil.width == 380
    assert loaded_pil.original_channels == 1


def test_rgba_input():
    """Test 11: RGBA 4-channel image handling."""
    # 4-channel NumPy array
    rgba_arr = np.full((300, 400, 4), 220, dtype=np.uint8)
    rgba_arr[:, :, 3] = 255  # Alpha
    loaded = load_image(rgba_arr)
    assert loaded.width == 400
    assert loaded.height == 300
    assert loaded.original_channels == 4
    assert loaded.rgb_array.shape == (300, 400, 3)

    # PIL 'RGBA' Image
    pil_rgba = Image.fromarray(rgba_arr, mode="RGBA")
    loaded_pil = load_image(pil_rgba)
    assert loaded_pil.original_channels == 4


def test_file_like_object():
    """Test loading from io.BytesIO buffer."""
    buf = io.BytesIO()
    img = Image.new("RGB", (320, 240), color=(100, 150, 200))
    img.save(buf, format="JPEG")
    buf.seek(0)

    loaded = load_image(buf)
    assert loaded.width == 320
    assert loaded.height == 240


def test_empty_bytes_raises_error():
    """Test empty byte input raises ImageLoadError."""
    with pytest.raises(ImageLoadError) as exc_info:
        load_image(b"")
    assert exc_info.value.error_code == "IMAGE_UNREADABLE"


def test_missing_file_raises_error():
    """Test missing file path raises ImageLoadError."""
    with pytest.raises(ImageLoadError) as exc_info:
        load_image("non_existent_path_to_file_12345.jpg")
    assert exc_info.value.error_code == "IMAGE_NOT_FOUND"


def test_corrupted_bytes_raises_error():
    """Test corrupt non-image bytes raise ImageFormatError."""
    with pytest.raises(ImageFormatError):
        load_image(b"CORRUPTED_NOT_AN_IMAGE_HEADER_DATA_12345")


def test_oversized_image_raises_error():
    """Test image exceeding max_dimension raises ImageSizeError."""
    cfg = DetectionConfig(max_dimension=500)
    arr = np.zeros((600, 400, 3), dtype=np.uint8)
    with pytest.raises(ImageSizeError) as exc_info:
        load_image(arr, config=cfg)
    assert exc_info.value.error_code == "IMAGE_TOO_LARGE"
