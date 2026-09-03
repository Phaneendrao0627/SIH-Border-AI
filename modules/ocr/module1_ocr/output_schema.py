# ============================================================
# AI-BASED FAKE IDENTITY & DOCUMENT SCREENING SYSTEM
# MODULE 1: OUTPUT JSON SCHEMA & ERROR CODES SPECIFICATION
# ============================================================

MODULE_NAME = "MODULE_1_OCR_EXTRACTION"
MODULE_VERSION = "1.0.0"
SCHEMA_VERSION = "2026.1"

# Standard System Error Code Enum
ERROR_CODES = {
    "ERR_NONE": {"code": "E000", "description": "Processing completed successfully with no errors"},
    "ERR_FILE_NOT_FOUND": {"code": "E001", "description": "Input image file could not be located"},
    "ERR_CORRUPT_PAYLOAD": {"code": "E002", "description": "Image file header is corrupt or unsupported format"},
    "ERR_QUALITY_REJECTED": {"code": "E003", "description": "Image quality is critically low (unreadable blur/darkness)"},
    "ERR_OCR_ENGINE_FAILURE": {"code": "E004", "description": "Tesseract OCR engine encountered an execution error"},
    "ERR_FACE_DETECTOR_FAILED": {"code": "E005", "description": "Face detection model failed or could not process frame"},
    "ERR_MRZ_CHECKSUM_MISMATCH": {"code": "E006", "description": "MRZ check digits failed mathematical verification"},
    "ERR_UNKNOWN_DOCUMENT_TYPE": {"code": "E007", "description": "Document layout does not match any known template"},
    "ERR_DATA_NORMALIZATION": {"code": "E008", "description": "Date or identity field normalization failed"},
    "ERR_MANUAL_REVIEW_FLAGGED": {"code": "E009", "description": "Document flagged for mandatory human operator review"},
    "ERR_INTERNAL_EXCEPTION": {"code": "E010", "description": "Unhandled internal pipeline exception"}
}


def create_document_output(document_type="UNKNOWN", request_id=None):
    """
    Factory creating empty standardized payload complying with SIH Multi-Module JSON Schema.
    """
    return {
        "module": MODULE_NAME,
        "module_version": MODULE_VERSION,
        "schema_version": SCHEMA_VERSION,
        "request_id": request_id,
        "timestamp": None,
        "input_file": None,
        "file_hash_sha256": None,
        "document_type": document_type,
        "status": "PROCESSED",
        "manual_review_required": False,
        "manual_review_reasons": [],
        "identity": {
            "full_name": None,
            "surname": None,
            "given_name": None,
            "nationality": None,
            "date_of_birth": None,
            "gender": None
        },
        "document": {
            "document_number": None,
            "date_of_issue": None,
            "date_of_expiry": None,
            "place_of_birth": None,
            "place_of_issue": None,
            "issuing_authority": None
        },
        "additional_information": {},
        "face_extraction": {
            "face_detected": False,
            "face_image_path": None,
            "confidence": 0.0,
            "bounding_box": None
        },
        "image_quality": {
            "quality_score": 100.0,
            "blur_status": "SHARP",
            "laplacian_variance": 0.0,
            "glare_percentage": 0.0,
            "resolution": "0x0",
            "deskew_angle_corrected": 0.0,
            "warnings": []
        },
        "verification": {
            "mrz_available": False,
            "mrz_valid": False,
            "mrz_validation_score": 0.0,
            "composite_check_valid": None,
            "completeness_score": 0.0,
            "consistency_score": 0.0,
            "confidence_score": 0.0,
            "confidence_level": "LOW",
            "field_comparisons": {}
        },
        "field_confidence": {},
        "error_codes": []
    }