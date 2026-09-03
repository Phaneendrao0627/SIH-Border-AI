"""
Privacy, PII masking, and identity tokenization utilities.
"""
import hashlib
import re
from typing import Any, Dict


def mask_document_number(doc_num: str) -> str:
    """
    Masks the document number to preserve auditability while preventing full PII exposure.
    Example: 'M1234567' -> 'M12****7', 'AB123456' -> 'AB****56'
    """
    if not doc_num or not isinstance(doc_num, str):
        return "[UNAVAILABLE]"
    
    clean = doc_num.strip()
    length = len(clean)
    if length <= 2:
        return "*" * length
    if length <= 4:
        return clean[0] + "*" * (length - 2) + clean[-1]
    if length <= 8:
        return clean[:2] + "*" * (length - 3) + clean[-1]
    
    # For longer numbers: keep first 2 and last 2 characters
    return clean[:2] + "*" * (length - 4) + clean[-2:]


def mask_name(name: str) -> str:
    """
    Masks person's name tokens.
    Example: 'JOHN DOE' -> 'J*** D**'
    """
    if not name or not isinstance(name, str):
        return "[UNAVAILABLE]"
    tokens = name.strip().split()
    masked_tokens = []
    for token in tokens:
        if len(token) <= 1:
            masked_tokens.append(token)
        elif len(token) == 2:
            masked_tokens.append(token[0] + "*")
        else:
            masked_tokens.append(token[0] + "*" * (len(token) - 1))
    return " ".join(masked_tokens)


def mask_date(date_str: str) -> str:
    """
    Masks day and month while retaining year for age auditability.
    Example: '1995-04-12' -> '1995-**-**'
    """
    if not date_str or not isinstance(date_str, str):
        return "[UNAVAILABLE]"
    # Match YYYY-MM-DD or DD-MM-YYYY
    match_iso = re.match(r"^(\d{4})[-/.]\d{2}[-/.]\d{2}$", date_str.strip())
    if match_iso:
        return f"{match_iso.group(1)}-**-**"
    match_dmy = re.match(r"^\d{2}[-/.]\d{2}[-/.](\d{4})$", date_str.strip())
    if match_dmy:
        return f"**-**-{match_dmy.group(1)}"
    return "****-**-**"


def generate_identity_token(name: str, dob: str, nationality: str) -> str:
    """
    Generates a deterministic, one-way pseudonymized SHA-256 token for duplicate matching.
    """
    canonical_str = f"{name.strip().upper()}|{dob.strip()}|{nationality.strip().upper()}"
    return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()[:16]


def sanitize_dict_for_logging(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Redacts sensitive fields for safe logging without leaking raw PII.
    """
    sanitized = dict(data)
    sensitive_keys = {
        "name", "document_number", "passport_number", "visa_number",
        "national_id_number", "date_of_birth", "dob"
    }
    for k, v in sanitized.items():
        if k in sensitive_keys and isinstance(v, str):
            if "name" in k:
                sanitized[k] = mask_name(v)
            elif "date" in k or "dob" in k:
                sanitized[k] = mask_date(v)
            else:
                sanitized[k] = mask_document_number(v)
    return sanitized
