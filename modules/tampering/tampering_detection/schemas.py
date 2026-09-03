"""Pydantic schemas and data models for Module 3: Tampering Detection."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class RiskLevel(str, Enum):
    """Forensic risk classification tiers."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class SeverityLevel(str, Enum):
    """Evidence severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RegionCoordinate(BaseModel):
    """Bounding box coordinates for a document region."""
    name: str = Field(..., description="Unique identifier for the region")
    x: int = Field(..., ge=0, description="Top-left X pixel coordinate")
    y: int = Field(..., ge=0, description="Top-left Y pixel coordinate")
    width: int = Field(..., gt=0, description="Region width in pixels")
    height: int = Field(..., gt=0, description="Region height in pixels")


class DocumentRegions(BaseModel):
    """Collection of document regions partitioned by semantic category."""
    photo: List[RegionCoordinate] = Field(default_factory=list, description="Photo / portrait regions")
    text: List[RegionCoordinate] = Field(default_factory=list, description="Text bounding boxes")
    stamp: List[RegionCoordinate] = Field(default_factory=list, description="Stamp / seal regions")


class ImageQualityMetrics(BaseModel):
    """Image resolution, clarity, and photometric properties."""
    width: int = Field(..., description="Image width in pixels")
    height: int = Field(..., description="Image height in pixels")
    channels: int = Field(..., description="Number of color channels")
    blur_score: float = Field(..., description="Variance of Laplacian blur metric")
    low_resolution: bool = Field(..., description="Flag indicating image is low resolution")
    is_overexposed: bool = Field(default=False, description="Flag indicating potential overexposure")
    is_underexposed: bool = Field(default=False, description="Flag indicating potential underexposure")
    contrast_score: float = Field(default=0.0, description="Grayscale standard deviation contrast metric")
    color_mode: str = Field(default="RGB", description="Input color space (RGB, RGBA, Grayscale)")
    was_resized: bool = Field(default=False, description="Whether the image was normalized or resized")


def sanitize_forensic_value(val: Any) -> Any:
    """Recursively convert numpy scalars and arrays to native Python JSON types."""
    import numpy as np
    if isinstance(val, (np.bool_, bool)):
        return bool(val)
    if isinstance(val, (np.floating, float)):
        return float(val)
    if isinstance(val, (np.integer, int)):
        return int(val)
    if isinstance(val, np.ndarray):
        return val.tolist()
    if isinstance(val, dict):
        return {str(k): sanitize_forensic_value(v) for k, v in val.items()}
    if isinstance(val, (list, tuple)):
        return [sanitize_forensic_value(v) for v in val]
    return val


class EvidenceItem(BaseModel):
    """Structured, explainable forensic evidence record."""
    detector: str = Field(..., description="Name of the detector generating this evidence")
    region_name: Optional[str] = Field(default=None, description="Name of the affected region if applicable")
    signal: str = Field(..., description="Machine-readable signal name")
    severity: SeverityLevel = Field(..., description="Signal severity tier")
    score_contribution: float = Field(..., ge=0.0, le=100.0, description="Points contributed to overall score")
    description: str = Field(..., description="Human-readable forensic rationale using cautious terminology")
    measurements: Dict[str, Any] = Field(default_factory=dict, description="Numerical measurements and metrics")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detector confidence in this specific finding")

    @field_validator("measurements", mode="before")
    @classmethod
    def sanitize_measurements(cls, v: Any) -> Any:
        if isinstance(v, dict):
            return {k: sanitize_forensic_value(val) for k, val in v.items()}
        return v


class RegionForensicDetail(BaseModel):
    """Detailed forensic evaluation for a specific sub-region."""
    region_name: str = Field(..., description="Name of the region analyzed")
    tampering_score: float = Field(..., ge=0.0, le=100.0, description="Region-specific tampering score")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in the region evaluation")
    signals: List[str] = Field(default_factory=list, description="Detected signals in this region")
    measurements: Dict[str, Any] = Field(default_factory=dict, description="Raw forensic metrics")
    warnings: List[str] = Field(default_factory=list, description="Region-specific warnings")
    evidence_summary: str = Field(default="", description="Summary of forensic findings")

    @field_validator("measurements", mode="before")
    @classmethod
    def sanitize_measurements(cls, v: Any) -> Any:
        if isinstance(v, dict):
            return {k: sanitize_forensic_value(val) for k, val in v.items()}
        return v


class MetadataAnalysisResult(BaseModel):
    """Forensic metadata and EXIF analysis findings."""
    available: bool = Field(default=False, description="Whether EXIF/metadata was present in the file")
    flags: List[str] = Field(default_factory=list, description="Metadata warning flags")
    software: Optional[str] = Field(default=None, description="Software tag detected in EXIF")
    timestamps: Dict[str, Optional[str]] = Field(default_factory=dict, description="Extracted timestamp tags")
    raw_safe_tags: Dict[str, Any] = Field(default_factory=dict, description="Sanitized EXIF tags without PII")
    score: float = Field(default=0.0, ge=0.0, le=100.0, description="Metadata tampering suspicion score")


class ElaAnalysisResult(BaseModel):
    """Error Level Analysis (ELA) statistical and regional findings."""
    enabled: bool = Field(default=True, description="Whether ELA analysis was performed")
    quality: int = Field(default=90, description="JPEG recompression quality level used")
    global_mean: float = Field(default=0.0, description="Mean ELA difference across whole document")
    global_std: float = Field(default=0.0, description="Standard deviation of ELA difference")
    global_p95: float = Field(default=0.0, description="95th percentile ELA difference")
    score: float = Field(default=0.0, ge=0.0, le=100.0, description="Global ELA anomaly score")
    anomaly_regions: List[str] = Field(default_factory=list, description="Regions with abnormal ELA deviations")
    limitations: List[str] = Field(
        default_factory=lambda: [
            "ELA is a forensic heuristic and may be affected by multiple compression cycles, resizing, or scanning."
        ],
        description="Forensic limitations and disclaimers",
    )


class PhotoAnalysisResult(BaseModel):
    """Photo replacement and portrait tampering analysis."""
    enabled: bool = Field(default=False, description="Whether photo analysis was performed")
    regions_analyzed: int = Field(default=0, description="Number of photo regions evaluated")
    photo_replacement_suspected: bool = Field(default=False, description="Whether photo replacement is suspected")
    score: Optional[float] = Field(default=None, ge=0.0, le=100.0, description="Photo tampering score")
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Photo analysis confidence")
    signals: List[str] = Field(default_factory=list, description="Detected photo anomalies")
    region_results: List[RegionForensicDetail] = Field(default_factory=list, description="Per-photo region metrics")
    reason: Optional[str] = Field(default=None, description="Reason if photo analysis was skipped")


class TextAnalysisResult(BaseModel):
    """Text manipulation and stroke consistency analysis."""
    enabled: bool = Field(default=False, description="Whether text analysis was performed")
    regions_analyzed: int = Field(default=0, description="Number of text regions evaluated")
    text_manipulation_suspected: bool = Field(default=False, description="Whether text alteration is suspected")
    score: Optional[float] = Field(default=None, ge=0.0, le=100.0, description="Text manipulation score")
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Text analysis confidence")
    signals: List[str] = Field(default_factory=list, description="Detected text anomalies")
    region_results: List[RegionForensicDetail] = Field(default_factory=list, description="Per-text region metrics")
    reason: Optional[str] = Field(default=None, description="Reason if text analysis was skipped")


class StampAnalysisResult(BaseModel):
    """Stamp forgery, texture, and copy-paste pattern analysis."""
    enabled: bool = Field(default=False, description="Whether stamp analysis was performed")
    regions_analyzed: int = Field(default=0, description="Number of stamp regions evaluated")
    stamp_forgery_suspected: bool = Field(default=False, description="Whether stamp forgery is suspected")
    score: Optional[float] = Field(default=None, ge=0.0, le=100.0, description="Overall stamp tampering score")
    texture_anomaly_score: Optional[float] = Field(default=None, ge=0.0, le=100.0, description="Texture anomaly score")
    duplicate_pattern_score: Optional[float] = Field(default=None, ge=0.0, le=100.0, description="Duplicate pattern score")
    ela_anomaly_score: Optional[float] = Field(default=None, ge=0.0, le=100.0, description="ELA anomaly score")
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Stamp analysis confidence")
    signals: List[str] = Field(default_factory=list, description="Detected stamp anomalies")
    region_results: List[RegionForensicDetail] = Field(default_factory=list, description="Per-stamp region metrics")
    reason: Optional[str] = Field(default=None, description="Reason if stamp analysis was skipped")


class TamperingAnalysisSummary(BaseModel):
    """Container for individual forensic sub-analyses."""
    metadata: MetadataAnalysisResult
    ela: ElaAnalysisResult
    photo_analysis: PhotoAnalysisResult
    text_analysis: TextAnalysisResult
    stamp_analysis: StampAnalysisResult


class ArtifactsResult(BaseModel):
    """Paths to optional visual forensic artifacts."""
    ela_map: Optional[str] = Field(default=None, description="Path to generated ELA heatmap image")
    ela_overlay: Optional[str] = Field(default=None, description="Path to generated ELA overlay image")
    region_visualizations: List[str] = Field(default_factory=list, description="Paths to bounding box visualization images")


class ProcessingInfo(BaseModel):
    """Execution profiling and detector audit trail."""
    elapsed_ms: float = Field(default=0.0, description="Total execution time in milliseconds")
    detectors_run: List[str] = Field(default_factory=list, description="List of detectors that executed")
    detectors_skipped: List[str] = Field(default_factory=list, description="List of detectors that were skipped")


class TamperingDetectionResult(BaseModel):
    """Master response schema for Module 3: Tampering Detection."""
    schema_version: str = Field(default="1.0", description="Schema version")
    document_id: Optional[str] = Field(default=None, description="Opaque identifier of document")
    document_type: str = Field(default="unknown", description="Type of travel document (passport, visa, id)")
    status: str = Field(default="completed", description="Analysis execution status")

    tampering_score: int = Field(..., ge=0, le=100, description="Overall tampering suspicion score (0-100)")
    risk_level: RiskLevel = Field(..., description="Risk tier: LOW, MEDIUM, HIGH, CRITICAL")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Holistic confidence score (0.0 to 1.0)")

    tampering_analysis: TamperingAnalysisSummary = Field(..., description="Detailed sub-analysis findings")

    flags: List[str] = Field(default_factory=list, description="Aggregated machine-readable anomaly flags")
    evidence: List[EvidenceItem] = Field(default_factory=list, description="Explainable human-readable evidence entries")
    warnings: List[str] = Field(default_factory=list, description="System and forensic advisory warnings")

    quality: ImageQualityMetrics = Field(..., description="Document image quality metrics")
    artifacts: ArtifactsResult = Field(default_factory=ArtifactsResult, description="Optional generated visual artifacts")
    processing: ProcessingInfo = Field(default_factory=ProcessingInfo, description="Execution performance details")
