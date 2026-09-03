"""
Input contract definition and schema validation for Module 2: Document Validation.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union
import uuid

from document_validation.models.flags import ValidationFlag


@dataclass
class ValidationInput:
    request_id: str
    document_type: str
    country_code: str
    name: str
    document_number: str
    date_of_birth: str
    date_of_issue: Optional[str] = None
    date_of_expiry: Optional[str] = None
    gender: Optional[str] = None
    visa_type: Optional[str] = None
    entry_validity: Optional[str] = None
    stay_duration: Optional[Union[int, str]] = None
    mrz_lines: List[str] = field(default_factory=list)
    mrz_checksum_score: Optional[float] = None
    ocr_confidence: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Store raw input representation for auditability
    raw_input: Dict[str, Any] = field(default_factory=dict)


def validate_and_parse_input(raw_data: Any) -> Tuple[Optional[ValidationInput], List[str], List[ValidationFlag]]:
    """
    Validates input schema, detects missing/null/empty/invalid types,
    and returns a normalized ValidationInput object or schema failure flags.
    
    Does NOT silently ignore missing mandatory fields.
    """
    errors: List[str] = []
    flags: List[ValidationFlag] = []

    if not isinstance(raw_data, dict):
        return (
            None,
            ["Input payload must be a JSON object / dictionary."],
            [ValidationFlag.INVALID_FIELD_TYPE, ValidationFlag.INCOMPLETE_DATA]
        )

    # 1. Check document_type
    doc_type = raw_data.get("document_type")
    if doc_type is None:
        errors.append("Field 'document_type' is missing or null.")
        flags.append(ValidationFlag.MISSING_DOCUMENT_TYPE)
    elif not isinstance(doc_type, str):
        errors.append("Field 'document_type' must be a string.")
        flags.append(ValidationFlag.INVALID_FIELD_TYPE)
    elif not doc_type.strip():
        errors.append("Field 'document_type' is empty.")
        flags.append(ValidationFlag.MISSING_DOCUMENT_TYPE)

    # 2. Check document_number (support document_number, passport_number, visa_number, national_id_number)
    doc_number = None
    for field_name in ["document_number", "passport_number", "visa_number", "national_id_number"]:
        if field_name in raw_data and raw_data[field_name] is not None:
            val = raw_data[field_name]
            if not isinstance(val, str):
                errors.append(f"Field '{field_name}' must be a string.")
                flags.append(ValidationFlag.INVALID_FIELD_TYPE)
            else:
                doc_number = val
            break
            
    if doc_number is None:
        # Check if the key was present as null
        has_key = any(k in raw_data for k in ["document_number", "passport_number", "visa_number", "national_id_number"])
        if has_key:
            errors.append("Document identifier field is null.")
        else:
            errors.append("Mandatory field 'document_number' (or equivalent) is missing.")
        flags.append(ValidationFlag.MISSING_DOCUMENT_NUMBER)
    elif isinstance(doc_number, str) and not doc_number.strip():
        errors.append("Document identifier field is empty string.")
        flags.append(ValidationFlag.MISSING_DOCUMENT_NUMBER)

    # 3. Check name
    name_val = raw_data.get("name")
    if name_val is None:
        errors.append("Field 'name' is missing or null.")
        flags.append(ValidationFlag.MISSING_NAME)
    elif not isinstance(name_val, str):
        errors.append("Field 'name' must be a string.")
        flags.append(ValidationFlag.INVALID_FIELD_TYPE)
    elif not name_val.strip():
        errors.append("Field 'name' is empty string.")
        flags.append(ValidationFlag.MISSING_NAME)

    # 4. Check country_code / nationality
    country_val = raw_data.get("country_code") or raw_data.get("nationality")
    if country_val is None:
        errors.append("Field 'country_code' or 'nationality' is missing or null.")
        flags.append(ValidationFlag.MISSING_NATIONALITY)
    elif not isinstance(country_val, str):
        errors.append("Field 'country_code' / 'nationality' must be a string.")
        flags.append(ValidationFlag.INVALID_FIELD_TYPE)
    elif not country_val.strip():
        errors.append("Field 'country_code' / 'nationality' is empty.")
        flags.append(ValidationFlag.MISSING_NATIONALITY)

    # 5. Check date_of_birth (or dob)
    dob_val = raw_data.get("date_of_birth") or raw_data.get("dob")
    if dob_val is None:
        errors.append("Field 'date_of_birth' (or 'dob') is missing or null.")
        flags.append(ValidationFlag.MISSING_DATE_OF_BIRTH)
    elif not isinstance(dob_val, str):
        errors.append("Field 'date_of_birth' must be a string.")
        flags.append(ValidationFlag.INVALID_FIELD_TYPE)
    elif not dob_val.strip():
        errors.append("Field 'date_of_birth' is empty.")
        flags.append(ValidationFlag.MISSING_DATE_OF_BIRTH)

    # Optional / Conditional fields
    issue_date_val = raw_data.get("date_of_issue") or raw_data.get("issue_date")
    if issue_date_val is not None and not isinstance(issue_date_val, str):
        errors.append("Field 'date_of_issue' must be a string if provided.")
        flags.append(ValidationFlag.INVALID_FIELD_TYPE)

    expiry_date_val = raw_data.get("date_of_expiry") or raw_data.get("expiry")
    if expiry_date_val is not None and not isinstance(expiry_date_val, str):
        errors.append("Field 'date_of_expiry' must be a string if provided.")
        flags.append(ValidationFlag.INVALID_FIELD_TYPE)

    gender_val = raw_data.get("gender")
    if gender_val is not None and not isinstance(gender_val, str):
        errors.append("Field 'gender' must be a string if provided.")
        flags.append(ValidationFlag.INVALID_FIELD_TYPE)

    # MRZ lines extraction
    mrz_lines: List[str] = []
    if "mrz_line_1" in raw_data and raw_data["mrz_line_1"]:
        if isinstance(raw_data["mrz_line_1"], str):
            mrz_lines.append(raw_data["mrz_line_1"])
    if "mrz_line_2" in raw_data and raw_data["mrz_line_2"]:
        if isinstance(raw_data["mrz_line_2"], str):
            mrz_lines.append(raw_data["mrz_line_2"])
    if "mrz_line_3" in raw_data and raw_data["mrz_line_3"]:
        if isinstance(raw_data["mrz_line_3"], str):
            mrz_lines.append(raw_data["mrz_line_3"])

    if not mrz_lines and "mrz" in raw_data and raw_data["mrz"]:
        mrz_raw = raw_data["mrz"]
        if isinstance(mrz_raw, str):
            mrz_lines = [l.strip() for l in mrz_raw.splitlines() if l.strip()]
        elif isinstance(mrz_raw, list):
            mrz_lines = [str(l).strip() for l in mrz_raw if str(l).strip()]

    # Checksum score & confidence
    mrz_conf = raw_data.get("mrz_checksum_score")
    if mrz_conf is None:
        mrz_conf = raw_data.get("valid_score")
    if mrz_conf is not None:
        try:
            mrz_conf = float(mrz_conf)
        except (ValueError, TypeError):
            errors.append("Field 'mrz_checksum_score' / 'valid_score' must be numeric.")
            flags.append(ValidationFlag.INVALID_FIELD_TYPE)
            mrz_conf = None

    ocr_conf = raw_data.get("ocr_confidence")
    if ocr_conf is not None:
        try:
            ocr_conf = float(ocr_conf)
        except (ValueError, TypeError):
            errors.append("Field 'ocr_confidence' must be numeric.")
            flags.append(ValidationFlag.INVALID_FIELD_TYPE)
            ocr_conf = None

    # Request ID
    req_id = raw_data.get("request_id")
    if not req_id or not isinstance(req_id, str):
        req_id = str(uuid.uuid4())

    meta = raw_data.get("metadata")
    if not isinstance(meta, dict):
        meta = {}

    if errors:
        flags.append(ValidationFlag.INCOMPLETE_DATA)
        return None, errors, flags

    parsed_input = ValidationInput(
        request_id=req_id,
        document_type=str(doc_type).strip(),
        country_code=str(country_val).strip().upper(),
        name=str(name_val).strip(),
        document_number=str(doc_number).strip(),
        date_of_birth=str(dob_val).strip(),
        date_of_issue=str(issue_date_val).strip() if issue_date_val else None,
        date_of_expiry=str(expiry_date_val).strip() if expiry_date_val else None,
        gender=str(gender_val).strip().upper() if gender_val else None,
        visa_type=str(raw_data.get("visa_type")).strip() if raw_data.get("visa_type") else None,
        entry_validity=str(raw_data.get("entry_validity")).strip() if raw_data.get("entry_validity") else None,
        stay_duration=raw_data.get("stay_duration"),
        mrz_lines=mrz_lines,
        mrz_checksum_score=mrz_conf,
        ocr_confidence=ocr_conf,
        metadata=meta,
        raw_input=dict(raw_data)
    )

    return parsed_input, [], []
