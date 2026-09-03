# Engineering Handover Guide — Module 3: Tampering Detection
### AI-Based Fake Identity & Document Screening System (SIH26188)

**To:** Downstream Integration Engineers (Backend, OCR, and Risk Scoring Teams)  
**From:** Senior Computer Vision & Image Forensics Engineer  
**Date:** September 2026  
**Status:** Complete & Production Ready  

---

## 1. Module Overview & Architectural Role

Module 3 is the standalone **Image Tampering Detection Engine** for the border screening system. Its sole objective is answering:
> *"Does the image of this travel/identity document show evidence of digital or physical alteration?"*

### Clear Separation of Concerns:
- **Module 1 (OCR & Layout)**: Extracts text strings and detects region bounding boxes.
- **Module 2 (Logical Validation)**: Checks checksums, date consistency, and MRZ formulas.
- **Module 3 (This Module)**: Detects pixel-level alterations, copy-paste artifacts, ELA compression discrepancies, stroke inconsistencies, and metadata editing history.
- **Module 4 (Biometric Face Match)**: Compares the document photo against the traveler's live webcam/camera feed.
- **Risk Scoring Engine**: Merges scores from Modules 2, 3, and 4 to make the final advisory recommendation.

**Module 3 does NOT perform OCR, face recognition, database lookups, or immigration decisions.**

---

## 2. Main Entrypoint Function

All downstream integrations should import and call the single unified entrypoint function:

```python
from tampering_detection import analyze_document, DetectionConfig

result = analyze_document(
    image_source,          # File path, bytes, BytesIO, PIL Image, or NumPy array
    document_id=None,      # Optional opaque string (e.g., 'DOC-88231')
    document_type="unknown", # e.g., 'passport', 'visa', 'id_card', 'driving_license'
    regions=None,          # Optional dictionary of region bounding boxes
    options=None,          # Optional DetectionConfig or dict
)
```

The function returns a strongly typed `TamperingDetectionResult` Pydantic model. To convert it into a standard Python dictionary or JSON string:

```python
# As a Python dictionary
result_dict = result.model_dump()

# As a JSON string
json_string = result.model_dump_json(indent=2)
```

---

## 3. Supported Image Input Formats

The `image_source` parameter accepts any of the following without requiring file-type conversions:

1. **Local File Path**: `str` or `pathlib.Path` (e.g. `"/path/to/doc.jpg"`).
2. **Raw Binary Bytes**: `bytes` (e.g. from an HTTP multipart upload `await file.read()`).
3. **File-Like Object**: `io.BytesIO` or standard file descriptor.
4. **PIL Image**: `PIL.Image.Image` instance.
5. **NumPy Array**: `np.ndarray` (OpenCV BGR, RGB, Grayscale 2D, or RGBA 4-channel).

Supported file formats: **JPEG / JPG, PNG, TIFF, BMP, WebP**.

---

## 4. How the OCR Team Passes Region Coordinates

The OCR and Layout Analysis team (Module 1) can optionally supply detected bounding boxes. Coordinates are measured in **pixels relative to the original image** with top-left origin `(0, 0)`.

### Region Structure Schema:
```python
regions = {
    "photo": [
        {
            "name": "document_photo",
            "x": 100,
            "y": 120,
            "width": 260,
            "height": 320
        }
    ],
    "text": [
        {
            "name": "date_of_birth",
            "x": 420,
            "y": 220,
            "width": 180,
            "height": 45
        },
        {
            "name": "passport_number",
            "x": 420,
            "y": 280,
            "width": 220,
            "height": 45
        }
    ],
    "stamp": [
        {
            "name": "entry_stamp_1",
            "x": 250,
            "y": 500,
            "width": 300,
            "height": 180
        }
    ]
}
```

### Critical Rules on Regions:
- **Regions are 100% Optional**: If `regions=None` or an empty dictionary is supplied, the module analyzes global document properties (EXIF metadata and full-document ELA) while gracefully skipping region-dependent checks.
- **Automatic Boundary Clamping**: If OCR provides coordinates exceeding document dimensions, Module 3 automatically clamps them and issues a non-fatal warning instead of crashing.
- **Sub-Threshold Region Filtering**: Extremely tiny boxes (e.g. `< 10x5` pixels) are flagged as `REGION_TOO_SMALL` and excluded from active modeling.

---

## 5. Interpreting the Output Schema

### Key Top-Level Fields:
- `tampering_score` (`int` between `0` and `100`): The aggregated suspicion score.
  - `0 - 29`: **LOW** risk. Document exhibits typical uniform characteristics.
  - `30 - 59`: **MEDIUM** risk. Minor anomalies detected (e.g. editing software in EXIF or moderate typography variance). Requires human spot-check.
  - `60 - 79`: **HIGH** risk. Substantial forensic anomalies (e.g. photo boundary step, high-frequency noise disparity, or cloned stamp).
  - `80 - 100`: **CRITICAL** risk. Multiple corroborated independent forensic indicators. Strong suspicion of forgery.
- `confidence` (`float` between `0.0` and `1.0`): Measurement of analysis reliability.
  - Reduced by blur, low resolution, extreme exposure, or missing regions.
  - Boosted by high clarity, full region coverage, and multi-detector agreement.
- `flags` (`List[str]`): Machine-readable alert tokens (e.g., `["editing_software_detected", "photo_replacement_suspected"]`).
- `evidence` (`List[EvidenceItem]`): Human-readable evidence items suitable for display on an officer's screen.
- `warnings` (`List[str]`): Informational alerts (e.g., `METADATA_UNAVAILABLE` or boundary clamping).
- `quality` (`ImageQualityMetrics`): Image clarity, blur score, and dimensions.
- `artifacts` (`ArtifactsResult`): Paths to generated visual heatmaps and overlays (if enabled).
- `processing` (`ProcessingInfo`): Execution latency in milliseconds and lists of active/skipped detectors.

---

## 6. Granular Sub-Analysis Fields

Within `result.tampering_analysis`:
- `metadata`: Contains `available`, `software`, `timestamps`, `raw_safe_tags`, and `score`.
- `ela`: Contains `global_mean`, `global_std`, `global_p95`, `score`, and `anomaly_regions`.
- `photo_analysis`: Contains `photo_replacement_suspected`, `score`, `signals`, and per-region measurements (`boundary_delta`, `noise_ratio`, `photo_ela_diff`).
- `text_analysis`: Contains `text_manipulation_suspected`, `score`, `signals`, and per-region measurements (`stroke_mean`, `pixel_density`, `has_flat_patch`).
- `stamp_analysis`: Contains `stamp_forgery_suspected`, `score`, `texture_anomaly_score`, `duplicate_pattern_score`, `ela_anomaly_score`, and per-stamp measurements.

---

## 7. Recoverable Warnings vs. Hard Exceptions

The module is built with strict fault-tolerance:

### Recoverable Warnings (Execution Continues):
- `METADATA_UNAVAILABLE`: Image has no EXIF tags (normal for web uploads, scans, or chat compression).
- `ELA_NOT_RELIABLE`: Image is a PNG or scan without native JPEG quantization baseline.
- `INVALID_REGION` / `REGION_TOO_SMALL`: Bad bounding boxes are clamped or skipped with warnings.
- `INSUFFICIENT_EVIDENCE`: Only 1 text region supplied, skipping cross-field comparison.
- `INTERNAL_DETECTOR_ERROR`: If an individual detector fails internally, it is caught, logged, and isolated. Remaining detectors run normally and weights are renormalized.

### Hard Exceptions (Raised when execution cannot proceed):
- `ImageLoadError`: Source file not found, empty byte stream, or invalid type.
- `ImageFormatError`: File header corrupted or non-image format.
- `ImageSizeError`: Dimensions exceed `max_dimension` (default 8192) or below minimum threshold.

---

## 8. Managing Visual Artifacts & Privacy

By default, **no files are written to disk** to uphold strict zero-leakage security.

### Enabling Visual Artifacts for Debugging or UI Demo:
```python
config = DetectionConfig(
    save_artifacts=True,
    artifacts_dir="/path/to/output_folder",
    privacy_mode=False
)
result = analyze_document(image_path, options=config)
```
When enabled, the following files are produced:
- `*_ela_heatmap.jpg`: JET colorized Error Level Analysis difference map.
- `*_ela_overlay.jpg`: Alpha-blended visualization over the document.
- `*_regions_overlay.jpg`: Bounding boxes color-coded by forensic severity (Green=Low, Orange=Medium, Red=High).

### Enforcing Strict Privacy:
When `privacy_mode=True`, artifact generation is disabled regardless of `save_artifacts` setting.

---

## 9. How Downstream Teams Can Swap or Extend Detectors

The module follows an open-closed design via `BaseDetector`:

```python
from tampering_detection.detectors.base import BaseDetector

class DeepLearningSplicingDetector(BaseDetector):
    def __init__(self):
        super().__init__(name="dl_splicing_analysis")

    def run(self, image, regions, config, context=None):
        # 1. Run custom deep learning model or heuristic
        # 2. Return result, list of EvidenceItem, list of warnings
        ...
```

Any new detector can be registered in `tampering_detection/api.py` without modifying the public `analyze_document` signature or breaking existing integrations.
