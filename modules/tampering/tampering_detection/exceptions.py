"""Custom exception hierarchy for the tampering detection package.

All exceptions inherit from TamperingDetectionError to allow callers
to catch module-level errors cleanly.
"""

from typing import Optional


class TamperingDetectionError(Exception):
    """Base exception for all tampering detection package errors."""

    def __init__(self, message: str, error_code: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "INTERNAL_ERROR"

    def __str__(self) -> str:
        return f"[{self.error_code}] {self.message}"


class ImageLoadError(TamperingDetectionError):
    """Raised when an image source cannot be found or read."""

    def __init__(self, message: str, error_code: str = "IMAGE_UNREADABLE"):
        super().__init__(message, error_code=error_code)


class ImageFormatError(TamperingDetectionError):
    """Raised when an unsupported image format is provided."""

    def __init__(self, message: str, error_code: str = "UNSUPPORTED_FORMAT"):
        super().__init__(message, error_code=error_code)


class ImageSizeError(TamperingDetectionError):
    """Raised when an image exceeds maximum dimensions or is below minimum size."""

    def __init__(self, message: str, error_code: str = "INVALID_IMAGE_DIMENSIONS"):
        super().__init__(message, error_code=error_code)


class InvalidRegionError(TamperingDetectionError):
    """Raised when region coordinates are malformed or invalid."""

    def __init__(self, message: str, error_code: str = "INVALID_REGION"):
        super().__init__(message, error_code=error_code)


class MetadataExtractionError(TamperingDetectionError):
    """Raised when metadata extraction fails critically."""

    def __init__(self, message: str, error_code: str = "METADATA_EXTRACTION_FAILED"):
        super().__init__(message, error_code=error_code)


class DetectorExecutionError(TamperingDetectionError):
    """Raised when a specific forensic detector encounters an unhandled error."""

    def __init__(self, message: str, detector_name: str, error_code: str = "INTERNAL_DETECTOR_ERROR"):
        super().__init__(f"Detector '{detector_name}' failed: {message}", error_code=error_code)
        self.detector_name = detector_name


class ConfigurationError(TamperingDetectionError):
    """Raised when invalid configuration parameters or weights are supplied."""

    def __init__(self, message: str, error_code: str = "CONFIG_ERROR"):
        super().__init__(message, error_code=error_code)
