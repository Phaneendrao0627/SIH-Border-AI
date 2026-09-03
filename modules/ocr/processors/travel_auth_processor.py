# ============================================================
# AI-BASED FAKE IDENTITY & DOCUMENT SCREENING SYSTEM
# MODULE 1: TRAVEL AUTHORIZATION PROCESSOR (ESTA / ETA / TRAVEL DOC)
# ============================================================

import re
from data_normalizer import normalize_date_iso, normalize_gender, normalize_nationality


def process_travel_authorization(raw_text, normalized_text):
    """
    Extracts structured fields from Electronic Travel Authorizations (ESTA/eTA/EVUS/ETA).
    """
    text = normalized_text

    def find_match(patterns):
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                return " ".join(m.group(1).strip().split())
        return None

    # Application / Authorization Number
    auth_number = find_match([
        r"(?:Authorization|Application|Reference|Confirmation|eTA)\s*(?:No|Number)?\s*[:\-]?\s*([A-Z0-9\-\/]{7,18})",
        r"\b([A-Z]\d{8,14})\b",
        r"\b(\d{10,16})\b"
    ])

    # Status (Approved, Authorized, Valid)
    auth_status = find_match([
        r"(?:Authorization\s*Status|Status)\s*[:\-]?\s*(AUTHORIZATION\s*APPROVED|APPROVED|VALID|ISSUED)",
        r"\b(AUTHORIZATION\s*APPROVED|APPROVED)\b"
    ]) or "APPROVED"

    # Full Name
    full_name = find_match([
        r"(?:Applicant\s*Name|Full\s*Name|Name|Nom)\s*[:\-]?\s*([A-Z\s]+?)(?=\n|DOB|Date|Passport|Nationality|$)",
        r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\b"
    ])

    surname = full_name.split()[-1] if full_name and len(full_name.split()) > 1 else None
    given_name = " ".join(full_name.split()[:-1]) if full_name and len(full_name.split()) > 1 else full_name

    # Passport Number
    passport_number = find_match([
        r"(?:Passport\s*(?:No|Number)|Document\s*Number)\s*[:\-]?\s*([A-Z0-9]{7,12})"
    ])

    # Nationality
    nationality = find_match([
        r"(?:Country\s*of\s*Citizenship|Nationality|Country)\s*[:\-]?\s*([A-Z\s]+?)(?=\n|$)"
    ])
    if nationality:
        nationality = normalize_nationality(nationality)

    # Date of Birth
    dob = find_match([
        r"(?:DOB|Date\s*of\s*Birth|Birth\s*Date)\s*[:\-]?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})"
    ])

    # Date of Issue / Authorization Date
    doi = find_match([
        r"(?:Date\s*of\s*Issue|Authorization\s*Date|Issued|Issue\s*Date)\s*[:\-]?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})"
    ])

    # Expiration Date
    doe = find_match([
        r"(?:Expiration\s*Date|Expiry\s*Date|Valid\s*Until|Expires)\s*[:\-]?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})"
    ])

    # Issuing Authority
    issuing_authority = find_match([
        r"(?:Issuing\s*Authority|Department|Agency)\s*[:\-]?\s*([A-Z\s]+?)(?=\n|$)",
        r"(Customs\s*and\s*Border\s*Protection|Department\s*of\s*Home\s*Affairs|Immigration\s*Authority)"
    ]) or "Border & Travel Authorization Agency"

    # Normalized ISO Dates
    dob_iso = normalize_date_iso(dob)
    doi_iso = normalize_date_iso(doi)
    doe_iso = normalize_date_iso(doe)

    fields = [auth_number, full_name, passport_number, doe_iso]
    valid_count = sum(1 for f in fields if f)
    conf_score = round((valid_count / len(fields)) * 100.0, 2)
    conf_level = "HIGH" if conf_score >= 75 else ("MEDIUM" if conf_score >= 50 else "LOW")

    return {
        "document_type": "TRAVEL_AUTHORIZATION",
        "status": "PROCESSED",
        "identity": {
            "full_name": full_name,
            "surname": surname,
            "given_name": given_name,
            "nationality": nationality,
            "date_of_birth": dob_iso,
            "gender": None
        },
        "document": {
            "document_number": auth_number,
            "passport_number": passport_number,
            "authorization_status": auth_status,
            "date_of_issue": doi_iso,
            "date_of_expiry": doe_iso,
            "place_of_birth": None,
            "issuing_authority": issuing_authority
        },
        "additional_information": {
            "authorization_number": auth_number,
            "authorization_status": auth_status,
            "associated_passport": passport_number,
            "issuing_authority": issuing_authority
        },
        "verification": {
            "mrz_available": False,
            "mrz_valid": False,
            "mrz_validation_score": 0.0,
            "completeness_score": conf_score,
            "confidence_score": conf_score,
            "confidence_level": conf_level
        }
    }
