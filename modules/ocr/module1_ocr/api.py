# ============================================================
# AI-BASED FAKE IDENTITY & DOCUMENT SCREENING SYSTEM
# MODULE 1: REST API SERVER (FLASK / CORS)
# ============================================================

import os
import sys
from datetime import datetime
from werkzeug.utils import secure_filename

# Configure module directory in sys.path
_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
if _MODULE_DIR not in sys.path:
    sys.path.insert(0, _MODULE_DIR)

# Configure UTF-8 encoding for Windows terminals
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

from flask import Flask, request, jsonify
from flask_cors import CORS

from app import process_document
from output_schema import MODULE_NAME, MODULE_VERSION, SCHEMA_VERSION, ERROR_CODES, create_document_output

PORT = int(os.environ.get("PORT", 5000))
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024 * 1024  # 32MB max upload limit


@app.route("/api/v1/health", methods=["GET"])
@app.route("/health", methods=["GET"])
@app.route("/", methods=["GET"])
def health_check():
    """Health check endpoint providing module status and version metadata."""
    return jsonify({
        "status": "HEALTHY",
        "module": MODULE_NAME,
        "module_version": MODULE_VERSION,
        "schema_version": SCHEMA_VERSION,
        "timestamp": datetime.now().isoformat()
    }), 200


@app.route("/api/v1/schema", methods=["GET"])
@app.route("/schema", methods=["GET"])
def get_schema():
    """Schema endpoint describing output structure and error codes."""
    return jsonify({
        "module": MODULE_NAME,
        "version": MODULE_VERSION,
        "schema_version": SCHEMA_VERSION,
        "error_codes": ERROR_CODES,
        "sample_output_template": create_document_output("SAMPLE")
    }), 200


@app.route("/api/v1/process", methods=["POST"])
@app.route("/api/screen-document", methods=["POST"])
@app.route("/process", methods=["POST"])
def screen_document():
    """
    Main screening endpoint.
    Accepts multipart/form-data with file field 'image' or 'file'.
    Optional form field: 'operator_id'.
    """
    file_item = None
    if "image" in request.files:
        file_item = request.files["image"]
    elif "file" in request.files:
        file_item = request.files["file"]

    if file_item is None or file_item.filename == "":
        return jsonify({
            "status": "ERROR",
            "error_code": "E001",
            "message": "No 'image' or 'file' field found in multipart/form-data upload"
        }), 400

    filename = secure_filename(file_item.filename) or "uploaded_doc.jpg"
    operator_id = request.form.get("operator_id", "OPERATOR_REST_API")

    save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    try:
        file_item.save(save_path)
        result = process_document(save_path, operator_id=operator_id)
        status_code = 200 if result.get("status") != "ERROR" else 422
        return jsonify(result), status_code
    except Exception as err:
        return jsonify({
            "status": "ERROR",
            "error_code": "E010",
            "message": f"Internal pipeline exception: {str(err)}"
        }), 500


def run_server(port=PORT):
    print("=" * 75)
    print(f"🚀 MODULE 1 SCREENING REST API SERVER RUNNING ON PORT {port}")
    print("=" * 75)
    print(f"  Health Check : GET  http://localhost:{port}/api/v1/health")
    print(f"  Schema Spec  : GET  http://localhost:{port}/api/v1/schema")
    print(f"  Process Doc  : POST http://localhost:{port}/api/v1/process")
    print("=" * 75)
    print("Press Ctrl+C to stop.\n")
    app.run(host="0.0.0.0", port=port, debug=False)


if __name__ == "__main__":
    run_server(PORT)

