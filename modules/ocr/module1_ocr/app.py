# ============================================================
# AI-BASED FAKE IDENTITY & DOCUMENT SCREENING SYSTEM
# MODULE 1: MASTER OCR & DOCUMENT SCREENING ORCHESTRATOR
# ============================================================

import os
import sys
import json
import argparse
import uuid
import cv2
import pytesseract
from datetime import datetime

# Configure module directory in sys.path
_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
if _MODULE_DIR not in sys.path:
    sys.path.insert(0, _MODULE_DIR)

# Configure UTF-8 output encoding for Windows PowerShell / CMD
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

# Local pipeline modules
from image_preprocessing import preprocess_document_image
from document_classifier import classify_document
from face_detector import detect_and_crop_face
from processors import process_by_type
from security import validate_input_file
from audit_logger import log_processing_event
from confidence_scorer import calculate_field_confidences, should_require_manual_review
from output_schema import MODULE_NAME, MODULE_VERSION, SCHEMA_VERSION, ERROR_CODES

# Configuration
DEFAULT_TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
DEFAULT_OUTPUT_DIR = "output"
DEFAULT_FINAL_JSON = os.path.join(DEFAULT_OUTPUT_DIR, "final_document.json")
DEFAULT_FACE_IMG = os.path.join(DEFAULT_OUTPUT_DIR, "face.jpg")


def setup_tesseract(custom_path=None):
    """Configures Tesseract executable path if present."""
    path = custom_path or DEFAULT_TESSERACT_PATH
    if os.path.exists(path):
        pytesseract.pytesseract.tesseract_cmd = path
    return os.path.exists(path)


def run_multi_pass_ocr(prep_data):
    """
    Runs multi-pass OCR across multiple binarization states, CLAHE contrast,
    bilateral filtering, and PSM modes (3, 6, 11).
    """
    gray_resized = prep_data["gray_resized"]
    clahe_enhanced = prep_data.get("clahe_enhanced", gray_resized)
    otsu_thresh = prep_data["otsu_thresh"]
    adaptive_thresh = prep_data["adaptive_thresh"]

    passes = [
        (gray_resized, "--psm 3"),
        (gray_resized, "--psm 6"),
        (clahe_enhanced, "--psm 6"),
        (otsu_thresh, "--psm 6"),
        (gray_resized, "--psm 11"),
        (adaptive_thresh, "--psm 11")
    ]

    all_texts = []
    for img, cfg in passes:
        try:
            txt = pytesseract.image_to_string(img, config=cfg)
            if txt and txt.strip():
                all_texts.append(txt.strip())
        except Exception:
            pass

    raw_text = "\n\n".join(all_texts)
    
    # Clean and normalize lines
    clean_lines = []
    for line in raw_text.splitlines():
        line = " ".join(line.strip().split())
        if line:
            clean_lines.append(line)
    
    normalized_text = "\n".join(clean_lines)
    return raw_text, normalized_text


def process_document(image_path, output_dir=DEFAULT_OUTPUT_DIR, tesseract_path=None, operator_id="OPERATOR_SYSTEM"):
    """
    End-to-end processing pipeline for Module 1.
    
    Pipeline Steps:
      1. Security & File Integrity Check (MIME/Magic bytes/SHA-256)
      2. Image Preprocessing & Quality Assessment (Laplacian, Glare, CLAHE, Deskew)
      3. Multi-Pass OCR (PSM 3, 6, 11)
      4. Document Type Classification
      5. Face Cropping for Module 4 (YuNet DNN Face Detector)
      6. Specialized Field Extraction & MRZ Checksum Validation
      7. Per-Field Confidence Scoring & Manual Review Trigger Evaluation
      8. Secure Audit Logging (Masked PII, Append-Only JSONL)
      9. Standardized Output Schema Assembly & JSON Persistence
    
    Returns:
        dict: Standardized document payload complying with SIH Multi-Module JSON Schema.
    """
    os.makedirs(output_dir, exist_ok=True)
    setup_tesseract(tesseract_path)
    request_id = str(uuid.uuid4())

    # 1. Security & File Validation
    is_valid, err_code, err_msg, file_hash = validate_input_file(image_path)
    if not is_valid:
        error_payload = {
            "module": MODULE_NAME,
            "module_version": MODULE_VERSION,
            "schema_version": SCHEMA_VERSION,
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            "input_file": os.path.abspath(image_path) if os.path.exists(image_path) else image_path,
            "file_hash_sha256": file_hash,
            "document_type": "UNKNOWN",
            "status": "ERROR",
            "manual_review_required": True,
            "manual_review_reasons": [err_msg],
            "error_codes": [err_code]
        }
        log_processing_event(
            request_id=request_id,
            file_path=image_path,
            file_hash=file_hash or "UNKNOWN",
            document_type="UNKNOWN",
            status="ERROR",
            confidence_score=0.0,
            confidence_level="LOW",
            manual_review_required=True,
            manual_review_reasons=[err_msg],
            operator_id=operator_id,
            error_code=err_code
        )
        return error_payload

    # 2. Image Preprocessing & Quality Assessment
    prep = preprocess_document_image(image_path)
    quality_report = prep["quality"]
    skew_angle = prep["skew_angle"]

    # 3. Multi-Pass OCR
    raw_text, normalized_text = run_multi_pass_ocr(prep)

    # 4. Document Classification
    detected_type = classify_document(normalized_text)

    # 5. Face Detection & Cropping (For Module 4)
    face_output_path = os.path.join(output_dir, "face.jpg")
    face_data = detect_and_crop_face(prep["original"], output_path=face_output_path)

    # 6. Route to Specialized Document Processor
    if detected_type == "PASSPORT":
        try:
            from passporteye import read_mrz
            pe = read_mrz(image_path)
            if pe and pe.to_dict():
                raw_text += "\n" + pe.to_dict().get("raw_text", "")
        except Exception:
            pass

    doc_result = process_by_type(detected_type, raw_text, normalized_text)

    identity_data = doc_result.get("identity", {})
    document_data = doc_result.get("document", {})
    verification_data = doc_result.get("verification", {})

    # 7. Per-Field Confidence Scoring
    field_confidences = calculate_field_confidences(
        identity=identity_data,
        document=document_data,
        verification=verification_data,
        quality_report=quality_report
    )

    # 8. Manual Review Trigger Evaluation
    overall_conf = verification_data.get("confidence_score", 0.0)
    manual_review_req, manual_review_reasons = should_require_manual_review(
        confidence_score=overall_conf,
        verification=verification_data,
        quality_report=quality_report,
        identity=identity_data,
        document=document_data
    )

    # 9. Assemble Final Standardized Schema
    final_payload = {
        "module": MODULE_NAME,
        "module_version": MODULE_VERSION,
        "schema_version": SCHEMA_VERSION,
        "request_id": request_id,
        "timestamp": datetime.now().isoformat(),
        "input_file": os.path.abspath(image_path),
        "file_hash_sha256": file_hash,
        "document_type": doc_result.get("document_type", detected_type),
        "status": doc_result.get("status", "PROCESSED"),
        "manual_review_required": manual_review_req,
        "manual_review_reasons": manual_review_reasons,
        "identity": identity_data,
        "document": document_data,
        "additional_information": doc_result.get("additional_information", {}),
        "face_extraction": {
            "face_detected": face_data.get("face_detected", False),
            "face_image_path": face_data.get("face_image_path"),
            "confidence": face_data.get("confidence", 0.0),
            "bounding_box": face_data.get("bounding_box")
        },
        "image_quality": {
            "quality_score": quality_report.get("quality_score"),
            "blur_status": quality_report.get("blur_status"),
            "laplacian_variance": quality_report.get("laplacian_variance"),
            "glare_percentage": quality_report.get("glare_percentage", 0.0),
            "resolution": quality_report.get("resolution"),
            "deskew_angle_corrected": skew_angle,
            "warnings": quality_report.get("warnings", [])
        },
        "verification": verification_data,
        "field_confidence": field_confidences,
        "raw_ocr_text": normalized_text[:1000] if normalized_text else "",
        "error_codes": [] if not manual_review_req else ["E009"]
    }

    # 10. Secure Audit Logging
    log_processing_event(
        request_id=request_id,
        file_path=image_path,
        file_hash=file_hash,
        document_type=final_payload["document_type"],
        status=final_payload["status"],
        confidence_score=overall_conf,
        confidence_level=verification_data.get("confidence_level", "LOW"),
        manual_review_required=manual_review_req,
        manual_review_reasons=manual_review_reasons,
        operator_id=operator_id,
        error_code="E009" if manual_review_req else None
    )

    # 11. Save Final JSON
    final_json_path = os.path.join(output_dir, "final_document.json")
    with open(final_json_path, "w", encoding="utf-8") as f:
        json.dump(final_payload, f, indent=4, ensure_ascii=False)

    return final_payload


def print_cli_summary(result):
    """Prints a beautiful, formatted terminal summary for demonstrations."""
    print("\n" + "=" * 75)
    print("      AI-BASED FAKE IDENTITY & DOCUMENT SCREENING SYSTEM")
    print("                     MODULE 1: OCR EXTRACTION")
    print("=" * 75)
    
    print(f"\n🔑 Request ID     : {result.get('request_id')}")
    print(f"🔒 SHA-256 Hash   : {result.get('file_hash_sha256')}")
    print(f"📂 Input File     : {result.get('input_file')}")
    print(f"📄 Document Type  : {result.get('document_type')}")
    print(f"⚡ Status         : {result.get('status')}")

    man_rev = result.get("manual_review_required", False)
    if man_rev:
        reasons_str = "; ".join(result.get("manual_review_reasons", []))
        print(f"⚠️ Manual Review  : REQUIRED ({reasons_str})")
    else:
        print(f"🛡️ Manual Review  : NOT NEEDED (Extraction Clean)")

    print("\n" + "-" * 75)
    print("👤 EXTRACTED IDENTITY INFORMATION")
    print("-" * 75)
    ident = result.get("identity", {})
    for k, v in ident.items():
        print(f"  {k.replace('_', ' ').title():<20} : {v if v else 'N/A'}")

    print("\n" + "-" * 75)
    print("📑 DOCUMENT DETAILS")
    print("-" * 75)
    doc = result.get("document", {})
    for k, v in doc.items():
        print(f"  {k.replace('_', ' ').title():<20} : {v if v else 'N/A'}")

    print("\n" + "-" * 75)
    print("🔍 VERIFICATION & QUALITY SUMMARY")
    print("-" * 75)
    ver = result.get("verification", {})
    face = result.get("face_extraction", {})
    qual = result.get("image_quality", {})

    print(f"  Face Detected      : {'✅ YES' if face.get('face_detected') else '❌ NO'} (Conf: {face.get('confidence')}%) -> {face.get('face_image_path')}")
    if ver.get("mrz_available"):
        print(f"  MRZ Available      : ✅ YES")
        print(f"  MRZ Checksum Valid : {'✅ YES' if ver.get('mrz_valid') else '❌ NO'} (Score: {ver.get('mrz_validation_score')}%)")
        if ver.get("composite_check_valid") is not None:
            print(f"  Composite Check    : {'✅ YES' if ver.get('composite_check_valid') else '❌ NO'}")
    print(f"  Image Sharpness    : {qual.get('blur_status')} (Score: {qual.get('quality_score')}%)")
    print(f"  Overall Confidence : {ver.get('confidence_score')}% [{ver.get('confidence_level')}]")

    comps = ver.get("field_comparisons", {})
    if comps:
        print("\n  Field Consistency Cross-Check:")
        for f, res in comps.items():
            sym = "✅" if res == "MATCH" else ("⚠️" if res == "DIFFERENT" else "❓")
            print(f"    - {f.replace('_', ' ').title():<20} : {sym} {res}")

    f_confs = result.get("field_confidence", {})
    if f_confs:
        print("\n  Per-Field Confidence Scores:")
        for f, score in f_confs.items():
            bar = "🟩" if score >= 80 else ("🟨" if score >= 50 else "🟥")
            print(f"    - {f.replace('_', ' ').title():<20} : {bar} {score}%")

    print("=" * 75)
    print(f"💾 Standardized JSON saved to: {os.path.join(DEFAULT_OUTPUT_DIR, 'final_document.json')}\n")


def start_api_server(port=5000):
    """Starts a production-grade Flask REST API for Modules 2, 3, and 4 integration."""
    try:
        from flask import Flask, request, jsonify
        from flask_cors import CORS
    except ImportError:
        print("❌ Flask / flask_cors not installed. Run: pip install Flask flask-cors")
        return

    api = Flask(__name__)
    CORS(api)

    @api.route("/api/v1/health", methods=["GET"])
    def health():
        return jsonify({
            "status": "HEALTHY",
            "module": MODULE_NAME,
            "module_version": MODULE_VERSION,
            "schema_version": SCHEMA_VERSION,
            "timestamp": datetime.now().isoformat()
        })

    @api.route("/api/v1/schema", methods=["GET"])
    def schema():
        from output_schema import create_document_output
        return jsonify({
            "module": MODULE_NAME,
            "schema_version": SCHEMA_VERSION,
            "error_codes": ERROR_CODES,
            "sample_output": create_document_output("SAMPLE")
        })

    @api.route("/api/v1/process", methods=["POST"])
    @api.route("/api/screen-document", methods=["POST"])
    def process_api():
        if "file" not in request.files and "image" not in request.files:
            return jsonify({"error": "No file uploaded. Use form field 'image' or 'file'"}), 400
        
        file = request.files.get("image") or request.files.get("file")
        operator_id = request.form.get("operator_id", "OPERATOR_API")

        os.makedirs("temp_uploads", exist_ok=True)
        upload_path = os.path.join("temp_uploads", file.filename)
        file.save(upload_path)

        try:
            res = process_document(upload_path, operator_id=operator_id)
            return jsonify(res), 200
        except Exception as err:
            return jsonify({
                "error": str(err),
                "error_code": "E010",
                "status": "ERROR"
            }), 500

    print(f"🚀 Starting Module 1 Screening REST API on http://localhost:{port}")
    print(f"   Endpoints:")
    print(f"     - POST http://localhost:{port}/api/v1/process")
    print(f"     - GET  http://localhost:{port}/api/v1/health")
    print(f"     - GET  http://localhost:{port}/api/v1/schema")
    api.run(host="0.0.0.0", port=port)


def main():
    parser = argparse.ArgumentParser(description="AI Document Screening - Module 1 OCR Engine")
    parser.add_argument("--image", "-i", default=os.path.join("input", "passport.jpg"), help="Path to document image")
    parser.add_argument("--all", "-a", action="store_true", help="Process all images in input directory")
    parser.add_argument("--server", "-s", action="store_true", help="Start Flask API Server")
    parser.add_argument("--port", "-p", type=int, default=5000, help="API server port")

    args = parser.parse_args()

    if args.server:
        start_api_server(port=args.port)
        return

    if args.all:
        input_dir = "input"
        if not os.path.exists(input_dir):
            print(f"Input directory '{input_dir}' not found.")
            return
        files = [f for f in os.listdir(input_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.bmp'))]
        print(f"\nProcessing {len(files)} document(s) in '{input_dir}'...\n")
        for idx, filename in enumerate(files, 1):
            filepath = os.path.join(input_dir, filename)
            print(f"[{idx}/{len(files)}] Processing {filename}...")
            try:
                res = process_document(filepath)
                print_cli_summary(res)
            except Exception as e:
                print(f"❌ Error processing {filename}: {e}")
        return

    # Process single image
    try:
        res = process_document(args.image)
        print_cli_summary(res)
    except Exception as e:
        print(f"❌ Execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

