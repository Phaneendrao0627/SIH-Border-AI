# ============================================================
# AI-BASED FAKE IDENTITY & DOCUMENT SCREENING SYSTEM
# MODULE 1: PROCESSORS PACKAGE
# ============================================================

from .passport_processor import process_passport
from .visa_processor import process_visa
from .national_id_processor import process_national_id
from .driving_license import process_driving_license
from .permit_processor import process_permit
from .travel_auth_processor import process_travel_authorization


def process_by_type(document_type, raw_text, normalized_text):
    """
    Routes document data to its specialized processor based on detected type.
    """
    doc_type_upper = str(document_type).upper().replace(" ", "_")

    if "PASSPORT" in doc_type_upper:
        return process_passport(raw_text, normalized_text)
    elif "VISA" in doc_type_upper:
        return process_visa(raw_text, normalized_text)
    elif "NATIONAL_ID" in doc_type_upper or "AADHAAR" in doc_type_upper:
        return process_national_id(raw_text, normalized_text)
    elif "DRIVING" in doc_type_upper or "LICENSE" in doc_type_upper or "LICENCE" in doc_type_upper:
        return process_driving_license(raw_text, normalized_text)
    elif "TRAVEL_AUTH" in doc_type_upper or "ESTA" in doc_type_upper or "ETA" in doc_type_upper:
        return process_travel_authorization(raw_text, normalized_text)
    elif "PERMIT" in doc_type_upper or "RESIDENCE" in doc_type_upper:
        return process_permit(raw_text, normalized_text)
    else:
        # Default fallback processor
        return {
            "document_type": "UNKNOWN",
            "status": "UNRECOGNIZED_TYPE",
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
                "issuing_authority": None
            },
            "additional_information": {
                "raw_text_snippet": normalized_text[:300] if normalized_text else ""
            },
            "verification": {
                "mrz_available": False,
                "mrz_valid": False,
                "mrz_validation_score": 0.0,
                "completeness_score": 0.0,
                "confidence_score": 20.0,
                "confidence_level": "LOW"
            }
        }

