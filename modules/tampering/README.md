# Module 3: Tampering Detection
### AI-Based Fake Identity & Document Screening System (SIH26188)

A standalone, production-ready digital image-forensics and physical document alteration detection Python package.

---

## 1. Project Purpose & Core Question

Border checkpoints and identity verification gates receive passports, visas, national IDs, driving permits, and residency cards. Fraudulent actors often generate documents with synthetically valid numbers and dates that pass traditional database checks while containing sophisticated physical or digital image alterations.

**Module 3 answers one central question:**
> *"Does the image of this document show forensic signs that it may have been digitally or physically altered?"*

This package delivers an explainable forensic evaluation covering portrait replacement, typography/text manipulation, stamp cloning, compression anomalies, and metadata history.

---

## 2. Features

- **Multi-Source Image Ingestion**: Ingests file paths, raw bytes, file-like `io.BytesIO` streams, `PIL.Image.Image`, and `numpy.ndarray` (RGB, BGR, Grayscale, RGBA).
- **Image Quality & Clarity Pre-Assessment**: Measures blur (Laplacian variance), resolution sufficiency, overexposure/underexposure, and contrast without penalizing fraud scores for low-quality inputs.
- **EXIF & Metadata Forensic Analysis**: Detects digital editing software signatures (Photoshop, GIMP, Canva, Affinity, Paint.NET, etc.), creation/modification timestamp discrepancies, and dimension inconsistencies with strict privacy filtering.
- **Error Level Analysis (ELA)**: Computes local compression artifact gradients using in-memory JPEG recompression and connected-component clustering.
- **Portrait Photo Replacement Detection**: Detects abrupt perimeter boundary steps, high-frequency noise variance mismatch between portrait and document paper substrate, and regional ELA deviations.
- **Text & Typography Manipulation Analysis**: Measures stroke width consistency (distance transform), foreground pixel density, edge density, and flat rectangular erase/paste artifacts.
- **Stamp Forgery & Pattern Duplication**: Texture classification via Local Binary Patterns (LBP), Shannon entropy, GLCM features, and cross-region visual cloning detection via perceptual hashing and normalized cross-correlation.
- **Dynamic Weight Renormalization**: Automatically adjusts detector weights when optional regions (photo, text, stamp) are omitted.
- **Forensic Explainability**: Employs strictly cautious forensic terminology (*"possible tampering"*, *"suspicious inconsistency"*, *"forensic heuristic"*, *"requires human review"*) with detailed quantitative metrics.
- **Zero Network Reliance**: 100% local execution using OpenCV, Pillow, NumPy, and scikit-image. Zero external API calls or telemetry.
- **Privacy Mode**: Disables disk writes and sanitizes all personal information and GPS tags.

---

## 3. Strict Scope Boundaries

| In Scope (Module 3) | Out of Scope (Handled by Other Modules) |
| :--- | :--- |
| Image loading, format normalization, and quality metrics | Frontend UI / Web application / Dashboard (React, HTML/CSS) |
| EXIF metadata extraction and editing software checks | Backend REST API server (FastAPI, Flask, Django) |
| Error Level Analysis (ELA) and difference heatmaps | Database storage or user authentication |
| Photo replacement & border splicing analysis | Optical Character Recognition (OCR) (Module 1) |
| Text field stroke, density, and patch inconsistency | Logical date/number validation (Module 2) |
| Stamp texture, flat background, and duplicate detection | Live face matching / biometric verification (Module 4) |
| Score aggregation, confidence estimation, and explainability | Government or police blacklist lookups |
| Local CLI testing tool and comprehensive unit tests | Final immigration clearance or legal decisions |

---

## 4. Installation

Requires **Python 3.10** or higher.

```bash
# Clone or navigate to the repository
cd TAMPERING_MODULE_3

# Install core dependencies
pip install -r requirements.txt

# Install the module in editable mode
pip install -e .
```

### Dependencies
- `numpy>=1.24.0`
- `opencv-python>=4.8.0`
- `pillow>=9.5.0`
- `scikit-image>=0.20.0`
- `scipy>=1.10.0`
- `exifread>=3.0.0`
- `pydantic>=2.0.0`
- `imagehash>=4.3.0`
- `pytest>=7.3.0` (Development & Testing)

---

## 5. Library Usage Example

```python
from tampering_detection import analyze_document, DetectionConfig

# 1. Define document image path (or pass raw bytes / PIL Image / NumPy array)
image_path = "samples/passport.jpg"

# 2. Optional: Region coordinates provided by upstream OCR / layout module
regions = {
    "photo": [
        {"name": "document_photo", "x": 100, "y": 120, "width": 260, "height": 320}
    ],
    "text": [
        {"name": "date_of_birth", "x": 420, "y": 220, "width": 180, "height": 45},
        {"name": "passport_number", "x": 420, "y": 280, "width": 220, "height": 45}
    ],
    "stamp": [
        {"name": "entry_stamp_1", "x": 250, "y": 500, "width": 300, "height": 180}
    ]
}

# 3. Optional: Configure options (or pass None for defaults)
options = DetectionConfig(
    privacy_mode=True,       # Suppress artifact generation on disk
    save_artifacts=False,
)

# 4. Execute forensic analysis
result = analyze_document(
    image_source=image_path,
    document_id="PASS-98231",
    document_type="passport",
    regions=regions,
    options=options,
)

# 5. Consume results
print(f"Tampering Score: {result.tampering_score}/100")
print(f"Risk Level:      {result.risk_level.value}")
print(f"Confidence:      {result.confidence}")
print(f"Anomaly Flags:   {result.flags}")

# Iterate over explainable evidence
for item in result.evidence:
    print(f"[{item.severity.value.upper()}] {item.detector}: {item.description}")
    print(f"  Measurements: {item.measurements}")
```

---

## 6. Command-Line Interface (CLI)

The CLI tool is designed strictly for local testing and developer validation:

```bash
# Basic usage
python -m tampering_detection.cli --image samples/passport.jpg

# Full forensic run with regions and visual artifact generation
python -m tampering_detection.cli \
  --image samples/passport.jpg \
  --document-id demo-001 \
  --document-type passport \
  --regions examples/sample_regions.json \
  --output results \
  --save-artifacts

# Strict privacy mode (suppresses visual artifact generation)
python -m tampering_detection.cli \
  --image samples/passport.jpg \
  --regions examples/sample_regions.json \
  --privacy-mode
```

### CLI Options:
- `--image`, `-i`: Path to document image file (**required**).
- `--document-id`: Opaque document ID string.
- `--document-type`: Document category (`passport`, `visa`, `id_card`).
- `--regions`, `-r`: Path to JSON file defining region bounding boxes.
- `--output`, `-o`: Directory to export generated reports and heatmaps.
- `--save-artifacts`: Generate and write visual heatmaps and overlays.
- `--privacy-mode`: Prevent all visual artifact generation.
- `--config`, `-c`: Path to custom JSON configuration.
- `--verbose`, `-v`: Output debug logs to `stderr`.

---

## 7. Region Coordinate JSON Format

Bounding boxes are defined in original pixel coordinates:

```json
{
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

*Note: All region categories are completely optional. If omitted, the module automatically skips the corresponding detector and renormalizes the weights across active detectors.*

---

## 8. Output Schema & Interpretation

The module outputs a structured, strongly typed Pydantic object serializable via `.model_dump()`:

```json
{
  "schema_version": "1.0",
  "document_id": "demo-001",
  "document_type": "passport",
  "status": "completed",
  "tampering_score": 72,
  "risk_level": "HIGH",
  "confidence": 0.85,
  "tampering_analysis": {
    "metadata": {
      "available": true,
      "flags": ["editing_software_detected"],
      "software": "Adobe Photoshop 2024",
      "timestamps": {
        "DateTime": "2024:05:10 14:22:01",
        "DateTimeOriginal": "2021:01:15 09:12:00"
      },
      "raw_safe_tags": { "Software": "Adobe Photoshop 2024" },
      "score": 45.0
    },
    "ela": {
      "enabled": true,
      "quality": 90,
      "global_mean": 0.62,
      "global_std": 1.51,
      "global_p95": 4.0,
      "score": 63.0,
      "anomaly_regions": ["document_photo"],
      "limitations": [
        "ELA is a forensic heuristic and may produce false positives after multiple saves, resizing, or scanning."
      ]
    },
    "photo_analysis": {
      "enabled": true,
      "regions_analyzed": 1,
      "photo_replacement_suspected": true,
      "score": 75.0,
      "confidence": 0.85,
      "signals": ["boundary_discontinuity", "noise_pattern_mismatch"],
      "region_results": [
        {
          "region_name": "document_photo",
          "tampering_score": 75.0,
          "confidence": 0.85,
          "signals": ["boundary_discontinuity", "noise_pattern_mismatch"],
          "measurements": {
            "boundary_delta": 165.06,
            "photo_noise_std": 15.32,
            "surrounding_noise_std": 0.32,
            "noise_ratio": 30.65
          },
          "warnings": [],
          "evidence_summary": "Photo region 'document_photo' evaluated."
        }
      ]
    },
    "text_analysis": {
      "enabled": true,
      "regions_analyzed": 2,
      "text_manipulation_suspected": false,
      "score": 0.0,
      "confidence": 0.8,
      "signals": [],
      "region_results": []
    },
    "stamp_analysis": {
      "enabled": false,
      "reason": "No stamp coordinates were provided.",
      "score": null
    }
  },
  "flags": [
    "editing_software_detected",
    "photo_replacement_suspected",
    "photo_boundary_discontinuity",
    "photo_noise_pattern_mismatch"
  ],
  "evidence": [
    {
      "detector": "photo_analysis",
      "region_name": "document_photo",
      "signal": "noise_pattern_mismatch",
      "severity": "medium",
      "score_contribution": 35.0,
      "description": "The high-frequency noise characteristics inside the photo region differ substantially from the immediately surrounding document background, suggesting splicing from an alternate camera or scan source.",
      "measurements": {
        "photo_noise_std": 15.32,
        "surrounding_noise_std": 0.32,
        "noise_ratio": 30.65,
        "configured_threshold": 1.6
      },
      "confidence": 0.85
    }
  ],
  "warnings": [
    "This module provides forensic indicators only and requires human review."
  ],
  "quality": {
    "width": 800,
    "height": 600,
    "channels": 3,
    "blur_score": 780.0,
    "low_resolution": false,
    "is_overexposed": false,
    "is_underexposed": false,
    "contrast_score": 30.01,
    "color_mode": "RGB",
    "was_resized": false
  },
  "artifacts": {
    "ela_map": "results/demo-001_ela_heatmap.jpg",
    "ela_overlay": "results/demo-001_ela_overlay.jpg",
    "region_visualizations": ["results/demo-001_regions_overlay.jpg"]
  },
  "processing": {
    "elapsed_ms": 112.4,
    "detectors_run": ["metadata", "ela", "photo", "text"],
    "detectors_skipped": ["stamp"]
  }
}
```

---

## 9. Scoring & Confidence Rationale

### Default Baseline Weights:
- **Metadata Analysis**: 10% (0.10)
- **Error Level Analysis (ELA)**: 30% (0.30)
- **Photo Replacement Analysis**: 25% (0.25)
- **Text Manipulation Analysis**: 20% (0.20)
- **Stamp Forgery Analysis**: 15% (0.15)

### Dynamic Weight Renormalization:
If an optional region (e.g. stamp) is omitted, its weight is redistributed proportionally among active detectors:
$$w'_i = \frac{w_i}{\sum_{j \in \text{active}} w_j}$$

### Risk Tiers:
- **LOW** (0 – 29): No meaningful forensic anomalies detected.
- **MEDIUM** (30 – 59): Mild anomalies detected (e.g. metadata software tag or minor typography variance).
- **HIGH** (60 – 79): Prominent anomalies (e.g., photo boundary step and noise mismatch).
- **CRITICAL** (80 – 100): Multiple corroborated independent anomalies across multiple modalities.

### Core Forensic Guardrails:
1. **Metadata-Only Cap**: Editing software tags alone cannot exceed 50.0 points and are strictly capped at MEDIUM risk.
2. **Critical Risk Requirement**: CRITICAL risk strictly requires multiple corroborating high-severity signals from independent detectors.
3. **Quality Decoupling**: Low resolution or blur reduces **confidence**, not increases fraud scores.

---

## 10. Privacy & Security Safeguards

- **Zero Data Leakage**: No images or data are sent over any network.
- **PII Protection**: Raw document images, passport numbers, names, and date-of-birth values are never written to log files.
- **EXIF Sanitization**: Camera serial numbers, GPS coordinates, owner names, and user comments are automatically filtered out before serialization.
- **Privacy Mode**: When `privacy_mode=True`, artifact generation is completely suppressed, preventing unauthorized disk caching.

---

## 11. Testing & Validation

Run the complete test suite covering all 22 required edge cases and scenarios:

```bash
# Run full test suite
python -m pytest tests/ -v

# Run synthetic evaluation benchmark
python examples/evaluate_synthetic_dataset.py
```

### Covered Test Cases:
1. Clean synthetic document baseline (`LOW` risk).
2. Editing software metadata detection (Photoshop / GIMP).
3. Stripped or missing EXIF metadata handling.
4. Photo replacement with sharp boundary discontinuity.
5. Photo region with noise standard deviation mismatch.
6. Text region with rectangular erased patch and stroke disparity.
7. Stamp region with cloned / duplicated visual pattern.
8. Native JPEG image ingestion.
9. Lossless PNG image ingestion.
10. Grayscale 1-channel image input.
11. RGBA 4-channel image input.
12. Blurry image detection and confidence penalty.
13. Very low-resolution image handling.
14. Out-of-bounds region coordinate clamping.
15. Missing region coordinates graceful fallback.
16. Sub-threshold tiny region filtering (`REGION_TOO_SMALL`).
17. Unhandled detector failure isolation without pipeline crash.
18. Mathematical consistency of weight renormalization.
19. Strict tampering score boundary enforcement `[0, 100]`.
20. JSON serialization compliance.
21. Artifact generation suppression when `save_artifacts=False`.
22. Strict disk write prevention in `privacy_mode=True`.

---

## 12. Forensic Limitations

1. **Error Level Analysis (ELA)** is a lossy-compression heuristic. It can produce elevated differences on scanned documents, screenshots, multiple save cycles, or images resized after editing.
2. **Metadata Flags** indicate editing software history but do not prove fraudulent intent (e.g., legitimate scanning software may embed software tags).
3. **Synthetic Benchmarks**: Synthetic test metrics are provided solely for pipeline verification and do not substitute for empirical calibration on physical checkpoint hardware.
4. **Advisory Role Only**: All outputs are probabilistic forensic indicators intended to assist human border inspection officers and must never be treated as legal decisions.
