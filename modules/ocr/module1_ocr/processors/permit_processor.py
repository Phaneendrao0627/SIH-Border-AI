# ============================================================
# AI-BASED FAKE IDENTITY & DOCUMENT SCREENING SYSTEM
# MODULE 1: PERMIT PROCESSOR (RESIDENCE / WORK / ENTRY PERMIT)
# ============================================================

import re
from data_normalizer import normalize_date_iso, normalize_gender, normalize_nationality


def process_permit(raw_text, normalized_text):
    """
    Extracts structured fields from Permit documents (Residence/Work/Entry/Travel).
    """
    text = normalized_text

    def find_match(patterns):
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                return " ".join(m.group(1).strip().split())
        return None

    # Permit / Authorization Number
    permit_number = find_match([
        r"(?:Permit|Authorization|Card|Registration)\s*(?:No|Number)?\s*[:\-]?\s*([A-Z0-9\-\/]{6,18})",
        r"\b([A-Z0-9]{8,14})\b"
    ])

    # Permit Type (Residence, Work, Student, Entry, Transit)
    permit_type = find_match([
        r"(?:Permit|Pass|Card)\s*Type\s*[:\-]?\s*([A-Z\s]+?)(?=\n|$)",
        r"(Residence|Work|Student|Entry|Travel|Permanent\s*Resident)\s*(?:Permit|Card|Authorization)",
        r"\b(RESIDENCE\s*PERMIT|WORK\s*PERMIT|STUDENT\s*PERMIT|TRAVEL\s*DOCUMENT)\b"
    ])

    # Holder Name
    full_name = find_match([
        r"(?:Name|Nom|Holder|Bearer|Applicant)\s*[:\-]?\s*([A-Z\s]+?)(?=\n|DOB|Date|Validity|Valid|$)",
        r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\b"
    ])

    # Nationality
    nationality = find_match([
        r"(?:Nationality|Country\s*of\s*Citizenship)\s*[:\-]?\s*([A-Z]+)"
    ])
    if nationality:
        nationality = normalize_nationality(nationality)

    # Date of Birth
    dob = find_match([
        r"(?:DOB|Date\s*of\s*Birth|Birth\s*Date)\s*[:\-]?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})"
    ])

    # Valid From / Date of Issue
    valid_from = find_match([
        r"(?:Valid\s*From|Date\s*of\s*Issue|Issue\s*Date|From)\s*[:\-]?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})"
    ])

    # Valid Until / Date of Expiry
    valid_until = find_match([
        r"(?:Validity|Valid\s*Until|Expiry\s*Date|Date\s*of\s*Expiry|Until)\s*[:\-]?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})"
    ])

    # Issuing Authority
    issuing_authority = find_match([
        r"(?:Issuing\s*Authority|Authority|Issued\s*By)\s*[:\-]?\s*([A-Z\s]+?)(?=\n|$)",
        r"(Immigration\s*(?:Department|Office|Bureau|Authority)|Home\s*Affairs|Ministry\s*of\s*Interior)"
    ]) or "Immigration / Home Affairs Department"

    # Normalized ISO Dates
    dob_iso = normalize_date_iso(dob)
    valid_from_iso = normalize_date_iso(valid_from)
    valid_until_iso = normalize_date_iso(valid_until)

    fields = [permit_number, full_name, valid_until]
    valid_count = sum(1 for f in fields if f)
    conf_score = round((valid_count / len(fields)) * 100.0, 2)
    conf_level = "HIGH" if conf_score >= 70 else ("MEDIUM" if conf_score >= 40 else "LOW")

    return {
        "document_type": "PERMIT",
        "status": "PROCESSED",
        "identity": {
            "full_name": full_name,
            "surname": full_name.split()[-1] if full_name and len(full_name.split()) > 1 else None,
            "given_name": " ".join(full_name.split()[:-1]) if full_name and len(full_name.split()) > 1 else full_name,
            "nationality": nationality,
            "date_of_birth": dob_iso,
            "gender": None
        },
        "document": {
            "document_number": permit_number,
            "permit_type": permit_type or "Residence Permit",
            "date_of_issue": valid_from_iso,
            "date_of_expiry": valid_until_iso,
            "valid_from": valid_from_iso,
            "valid_until": valid_until_iso,
            "place_of_birth": None,
            "issuing_authority": issuing_authority
        },
        "additional_information": {
            "permit_number": permit_number,
            "permit_type": permit_type or "Residence Permit",
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

