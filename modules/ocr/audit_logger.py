# ============================================================
# AI-BASED FAKE IDENTITY & DOCUMENT SCREENING SYSTEM
# MODULE 1: SECURE AUDIT & COMPLIANCE LOGGER
# ============================================================

import os
import json
import re
from datetime import datetime

LOGS_DIR = "logs"


def mask_sensitive_pii(data):
    """
    Masks sensitive personal identity numbers (e.g., Aadhaar 12-digit numbers)
    in log records to comply with data protection regulations.
    """
    if isinstance(data, dict):
        masked = {}
        for k, v in data.items():
            if k in ["id_number", "aadhaar_number", "vid"] and isinstance(v, str):
                digits = re.sub(r"\s+", "", v)
                if len(digits) == 12:
                    masked[k] = f"XXXX-XXXX-{digits[-4:]}"
                elif len(digits) == 16:
                    masked[k] = f"XXXX-XXXX-XXXX-{digits[-4:]}"
                else:
                    masked[k] = v[:2] + "X" * (len(v) - 4) + v[-2:] if len(v) > 4 else "XXXX"
            elif isinstance(v, (dict, list)):
                masked[k] = mask_sensitive_pii(v)
            else:
                masked[k] = v
        return masked
    elif isinstance(data, list):
        return [mask_sensitive_pii(item) for item in data]
    return data


def log_processing_event(
    request_id,
    file_path,
    file_hash,
    document_type,
    status,
    confidence_score,
    confidence_level,
    manual_review_required,
    manual_review_reasons=None,
    operator_id="OPERATOR_SYSTEM",
    error_code=None,
    output_dir=LOGS_DIR
):
    """
    Appends an immutable, structured JSONL audit record for every screened document.
    """
    os.makedirs(output_dir, exist_ok=True)
    today_str = datetime.now().strftime("%Y%m%d")
    log_file = os.path.join(output_dir, f"audit_{today_str}.jsonl")

    event = {
        "event_type": "DOCUMENT_SCREENING_OCR",
        "timestamp": datetime.now().isoformat(),
        "request_id": request_id,
        "operator_id": operator_id,
        "input_file_name": os.path.basename(file_path),
        "file_hash_sha256": file_hash,
        "document_type": document_type,
        "status": status,
        "confidence_score": confidence_score,
        "confidence_level": confidence_level,
        "manual_review_required": manual_review_required,
        "manual_review_reasons": manual_review_reasons or [],
        "error_code": error_code
    }

    masked_event = mask_sensitive_pii(event)

    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(masked_event, ensure_ascii=False) + "\n")
        return True
    except Exception as e:
        print(f"⚠️ Failed to write audit log: {e}")
        return False
