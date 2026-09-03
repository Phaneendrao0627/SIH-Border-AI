"""Configuration settings, thresholds, and weights for tampering detection."""

from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field


DEFAULT_SUSPICIOUS_SOFTWARE_KEYWORDS: List[str] = [
    "photoshop",
    "gimp",
    "imagemagick",
    "canva",
    "affinity",
    "snapseed",
    "corel",
    "paint.net",
    "pixlr",
    "photopea",
    "seashore",
    "lightroom",
    "picsart",
    "facetune",
    "pixelmator",
]


class DetectionConfig(BaseModel):
    """Central configuration class for tampering detection thresholds and weights."""

    # Detector Weights (sum should be 1.0)
    weight_metadata: float = Field(default=0.10, ge=0.0, le=1.0)
    weight_ela: float = Field(default=0.30, ge=0.0, le=1.0)
    weight_photo: float = Field(default=0.25, ge=0.0, le=1.0)
    weight_text: float = Field(default=0.20, ge=0.0, le=1.0)
    weight_stamp: float = Field(default=0.15, ge=0.0, le=1.0)

    # Risk Classification Thresholds
    threshold_low: int = Field(default=30, ge=1, le=100, description="Upper bound for LOW risk (0-29)")
    threshold_medium: int = Field(default=60, ge=1, le=100, description="Upper bound for MEDIUM risk (30-59)")
    threshold_high: int = Field(default=80, ge=1, le=100, description="Upper bound for HIGH risk (60-79); 80+ is CRITICAL")

    # Image Quality Thresholds
    blur_threshold: float = Field(default=80.0, ge=0.0, description="Laplacian variance threshold for blur")
    min_width: int = Field(default=350, ge=50)
    min_height: int = Field(default=250, ge=50)
    max_dimension: int = Field(default=8192, ge=100)
    min_contrast_std: float = Field(default=15.0, ge=0.0)
    exposure_outlier_ratio: float = Field(default=0.25, ge=0.0, le=1.0)

    # ELA Parameters
    ela_jpeg_quality: int = Field(default=90, ge=50, le=100)
    ela_anomaly_sigma: float = Field(default=2.5, ge=1.0)
    ela_min_component_size: int = Field(default=25, ge=1)
    ela_scale_factor: float = Field(default=15.0, ge=1.0)

    # Photo Region Parameters
    photo_boundary_strip_width: int = Field(default=8, ge=2, le=30)
    photo_noise_ratio_threshold: float = Field(default=1.60, ge=1.0)
    photo_color_delta_threshold: float = Field(default=25.0, ge=0.0)
    photo_ela_delta_threshold: float = Field(default=8.0, ge=0.0)

    # Text Region Parameters
    text_density_delta_threshold: float = Field(default=0.22, ge=0.0)
    text_stroke_variance_threshold: float = Field(default=0.25, ge=0.0)
    text_contrast_variance_threshold: float = Field(default=0.25, ge=0.0)
    text_ela_diff_threshold: float = Field(default=8.0, ge=0.0)
    text_min_region_width: int = Field(default=15, ge=2)
    text_min_region_height: int = Field(default=8, ge=2)

    # Stamp Region Parameters
    stamp_lbp_points: int = Field(default=16, ge=4)
    stamp_lbp_radius: int = Field(default=2, ge=1)
    stamp_flat_background_threshold: float = Field(default=1.0, ge=0.0)
    duplicate_hash_threshold: int = Field(default=5, ge=0, le=64)
    duplicate_template_threshold: float = Field(default=0.85, ge=0.0, le=1.0)

    # Metadata Settings
    suspicious_software_keywords: List[str] = Field(default_factory=lambda: list(DEFAULT_SUSPICIOUS_SOFTWARE_KEYWORDS))

    # Privacy & Operational Settings
    privacy_mode: bool = Field(default=False, description="When true, strictly disables saving artifacts to disk")
    save_artifacts: bool = Field(default=False, description="Whether to write visual heatmaps/overlays to disk")
    artifacts_dir: Optional[str] = Field(default=None, description="Directory to write visual artifacts")

    def get_effective_save_artifacts(self) -> bool:
        """Enforce privacy rule: if privacy_mode is True, artifact saving is disabled."""
        if self.privacy_mode:
            return False
        return self.save_artifacts
