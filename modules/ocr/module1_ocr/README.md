# AI-Based Fake Identity & Document Screening System (SIH26188)
## Module 1: OCR Extraction & Document Screening Pipeline

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://python.org)
[![OpenCV](https://img.shields.io/badge/OpenCV-5.0%2F4.10-green.svg)](https://opencv.org)
[![Tesseract OCR](https://img.shields.io/badge/Tesseract-v5.x-orange.svg)](https://github.com/tesseract-ocr/tesseract)
[![Tests](https://img.shields.io/badge/Tests-5%2F5%20Passed-brightgreen.svg)]()

Module 1 is the foundational computer vision and intelligence layer of the **AI-Based Fake Identity & Document Screening System**. It autonomously analyzes identity and travel documents (Passports, Visas, National IDs, Driving Licenses, and Permits), assesses image quality, corrects skew, performs multi-pass OCR, parses and validates Machine Readable Zones (MRZ) using ICAO 9303 checksums, crops the portrait photograph for **Module 4 (Face Verification)**, and generates standardized structured JSON for **Module 2 (Validation)** and **Module 3 (Tampering Detection)**.

---

##  Architecture & Pipeline Flow

```
                         DOCUMENT IMAGE
                                │
                                ▼
        ┌────────────────────────────────────────────────┐
        │ 1. Image Quality Assessment & Preprocessing    │
        │    - Laplacian Blur Scoring                    │
        │    - Over/Under-exposure Detection             │
        │    - Contour-based Auto-Deskewing (0° upright) │
        │    - Grayscale, 2x Upscaling, Otsu & Adaptive  │
        └───────────────────────┬────────────────────────┘
                                │
                                ▼
        ┌────────────────────────────────────────────────┐
        │ 2. SOTA Face Detection & Portrait Cropping     │
        │    - OpenCV YuNet DNN Detector (~230 KB)       │
        │    - 25% Proportional Padding Crop             │
        │    - Saves output/face.jpg (For Module 4)      │
        └───────────────────────┬────────────────────────┘
                                │
                                ▼
        ┌────────────────────────────────────────────────┐
        │ 3. Multi-Pass Tesseract OCR                    │
        │    - Passes 1 & 2: PSM 6 (Uniform text blocks) │
        │    - Passes 3 & 4: PSM 11 (Sparse text)        │
        └───────────────────────┬────────────────────────┘
                                │
                                ▼
        ┌────────────────────────────────────────────────┐
        │ 4. Document Classification                     │
        │    - Passport / Visa / National ID / DL /      │
        │      Permit / Unknown                          │
        └───────────────────────┬────────────────────────┘
                                │
        ┌───────────────────────┴────────────────────────┐
        ▼                                                ▼
┌───────────────────────────────┐        ┌───────────────────────────────┐
│ Specialized Document Routing  │        │ Passport MRZ Engine (ICAO)    │
│ - Visa Processor              │        │ - TD3 / TD2 / TD1 MRZ parsing │
│ - National ID (Aadhaar)       │        │ - 7-3-1 Weight Modulo 10      │
│ - Driving License             │        │   Check-digit Validation      │
│ - Permit Processor            │        │ - OCR Glitch & Noise Repair   │
└───────────────┬───────────────┘        └───────────────┬───────────────┘
                │                                        │
                └───────────────────┬────────────────────┘
                                    │
                                    ▼
        ┌────────────────────────────────────────────────┐
        │ 5. Field Consistency & Confidence Scoring      │
        │    - Cross-checking MRZ vs Visual OCR Text     │
        │    - Date & Country Code Normalization (ISO)   │
        │    - Weighted Confidence Index (HIGH/MED/LOW)  │
        └───────────────────────┬────────────────────────┘
                                │
                                ▼
        ┌────────────────────────────────────────────────┐
        │ 6. Standardized JSON Output (Module 2 & 3)     │
        │    - output/final_document.json                │
        └────────────────────────────────────────────────┘
```

---

##  Project Structure

```
module1_ocr/
│
├── app.py                      # Master Orchestrator (CLI, Batch, and REST API)
├── image_preprocessing.py      # Blur detection, brightness checks, auto-deskewing
├── face_detector.py            # YuNet DNN face detection & portrait cropping
├── document_classifier.py      # Rule-based document type classifier
├── test_pipeline.py            # Automated regression test suite (5/5 passed)
├── requirements.txt            # Python dependencies
├── README.md                   # System documentation
│
├── processors/                 # Modular document handlers
│   ├── __init__.py             # Router factory
│   ├── passport_processor.py   # MRZ TD3/TD2 parsing, checksums, visual OCR
│   ├── visa_processor.py       # Visa number, type, issuing post, validity
│   ├── national_id_processor.py# Aadhaar 12-digit format, full name, DOB, gender
│   ├── driving_license.py      # DL number, name, DOB, expiry
│   └── permit_processor.py     # Permit number, holder, type, validity
│
├── input/                      # Sample document images
│   ├── passport.jpg
│   ├── passport2.jpg
│   ├── visa.jpg
│   ├── national_id.jpg
│   └── driving_license.jpg.jpeg
│
└── output/                     # Generated outputs
    ├── face.jpg                # Cropped face portrait for Module 4
    ├── preprocessed.jpg        # Cleaned/deskewed image
    └── final_document.json     # Standardized JSON output payload
```

---

##  Getting Started

### 1. Prerequisites
- **Python 3.10+** (tested on Python 3.12)
- **Tesseract OCR** installed at `C:\Program Files\Tesseract-OCR\tesseract.exe` (or in system PATH)

### 2. Setup Virtual Environment & Install Dependencies
```bash
# Navigate to module folder
cd module1_ocr

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

##  Usage & Commands

### 1. Process a Single Document
```bash
python app.py --image input/passport.jpg
```

### 2. Batch Process All Documents in `input/`
```bash
python app.py --all
```

### 3. Start REST API Server (For Team Integration)
```bash
python app.py --server --port 5000
```
- **Health check:** `GET http://localhost:5000/api/health`
- **Screen document:** `POST http://localhost:5000/api/screen-document` (multipart/form-data with key `file`)

### 4. Run Automated Test Suite
```bash
python test_pipeline.py
```

---

## 🔗 Downstream Integration Contract

### Hand-off to Module 4 (Face Verification)
- **File:** `output/face.jpg`
- **Metadata in JSON:**
  ```json
  "face_extraction": {
      "face_detected": true,
      "face_image_path": "output\\face.jpg",
      "confidence": 92.79,
      "bounding_box": [228, 85, 211, 284]
  }
  ```

### Hand-off to Module 2 (Validation) & Module 3 (Tampering Detection)
- **File:** `output/final_document.json`
- **Sample Schema:**
  ```json
  {
      "module": "MODULE_1_OCR_EXTRACTION",
      "timestamp": "2026-09-02T10:40:18.543028",
      "input_file": ".../input/passport.jpg",
      "document_type": "PASSPORT",
      "status": "VERIFIED",
      "identity": {
          "full_name": "MADHAVI ATTHI",
          "surname": "ATTHI",
          "given_name": "MADHAVI",
          "nationality": "IND",
          "date_of_birth": "1982-04-06",
          "gender": "F"
      },
      "document": {
          "document_number": "P3938806",
          "date_of_issue": null,
          "date_of_expiry": "2026-08-28",
          "place_of_birth": "Dank",
          "place_of_issue": null
      },
      "image_quality": {
          "quality_score": 100.0,
          "blur_status": "SHARP",
          "laplacian_variance": 242.69,
          "resolution": "1280x741",
          "deskew_angle_corrected": 0.0,
          "warnings": []
      },
      "verification": {
          "mrz_available": true,
          "mrz_valid": true,
          "mrz_validation_score": 100.0,
          "completeness_score": 100.0,
          "confidence_score": 100.0,
          "confidence_level": "HIGH",
          "field_comparisons": {
              "passport_number": "MATCH",
              "surname": "MATCH"
          }
      }
  }
  ```

---

