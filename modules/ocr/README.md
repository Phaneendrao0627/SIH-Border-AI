# AI-Based Fake Identity & Document Screening System (SIH26188)
Ministry of Home Affairs | Smart India Hackathon

## System Architecture

The complete system consists of 4 interoperable modules:
- **Module 1 (OCR Extraction & Document Screening):** Preprocessing, MRZ & OCR field extraction, quality assessment, and face cropping. *(Located in [`module1_ocr/`](module1_ocr/))*
- **Module 2 (Document Validation):** Rule-based validation against official document standards.
- **Module 3 (Tampering Detection):** Photo replacement, font alteration, stamp forgery, and metadata analysis.
- **Module 4 (Face Verification):** Matches the cropped document photograph (`output/face.jpg`) with a live subject capture.

---

## Quick Start (Module 1)

```bash
cd module1_ocr
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Run on a document
python app.py --image input/passport.jpg

# Run automated tests
python test_pipeline.py
```

For full documentation and API specifications, see [`module1_ocr/README.md`](module1_ocr/README.md).
