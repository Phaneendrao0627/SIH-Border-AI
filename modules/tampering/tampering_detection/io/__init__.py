"""I/O utilities for image and metadata ingestion."""

from tampering_detection.io.image_loader import LoadedImage, load_image
from tampering_detection.io.metadata_reader import extract_metadata

__all__ = ["LoadedImage", "load_image", "extract_metadata"]
