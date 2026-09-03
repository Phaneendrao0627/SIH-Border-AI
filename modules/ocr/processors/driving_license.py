# ============================================================
# AI-BASED FAKE IDENTITY & DOCUMENT SCREENING SYSTEM
# MODULE 1: DRIVING LICENSE PROCESSOR
# ============================================================

import re
from data_normalizer import normalize_date_iso, normalize_gender


def process_driving_license(raw_text, normalized_text):
    """
    Extracts structured fields from Indian Driving License documents.
    """
    # Use both raw and normalized text for maximum coverage
    text = raw_text + "\n" + normalized_text

    def find_first(patterns, search_text=None):
        t = search_text if search_text is not None else text
        for pat in patterns:
            m = re.search(pat, t, re.IGNORECASE)
            if m:
                return " ".join(m.group(1).strip().split())
        return None

    # --- DL Number ---
    dl_number = find_first([
        r"\b([A-Z]{2}\d{13,16})\b",
        r"(?:DL|License|Licence)\s*(?:No|Number)?\s*[:\-]?\s*([A-Z]{2}\d{13,16})",
        r"\b([A-Z]{2}[-\s]?\d{2}[-\s]?\d{11,14})\b",
        r"(?:DL|License|Licence)\s*(?:No|Number)?\s*[:\-]?\s*([A-Z0-9\-\/]{8,20})"
    ])

    # --- Full Name ---
    # OCR produces: "Name . POOJARI ARJUN GOUD" or "Name ; POOJARI ARJUN GOUD"
    # Also handles POOJAR!I (OCR misreads I as !I)
    full_name = find_first([
        r"Name\s*[:\-\._;]?\s*([A-Z][A-Z!\s]{3,40}?)(?=\s*(?:Date|DOB|Holder|aides|alae|ae|sur|\"|\n|$))",
        r"Name\s*[:\-\._;]?\s*([A-Z][A-Z!\s]+?)(?=\n|$)",
        r"(?:Holder|Driver)\s*[:\-]?\s*([A-Z][A-Z!\s]+?)(?=\n|$)"
    ])
    if full_name:
        # Clean OCR noise: !I -> I, trailing junk
        full_name = full_name.replace("!", "")
        full_name = re.sub(r"\s+(ae|aides|Sigratze|SS|SJ|wer|var|sur|Ave|alae|Sppase)\s*$", "", full_name, flags=re.IGNORECASE).strip()
        full_name = " ".join(full_name.split())

    # --- Date of Birth ---
    dob = find_first([
        r"(?:DOB|Date\s*[Oo][f!]\s*Birth)\s*[:\-\.;]?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})"
    ])

    # --- Issue Date ---
    # OCR produces "Issue Date" label on one line, date on next line, or same line
    # Also handles colon-separated dates like 23:03:2024
    doi = find_first([
        r"(?:Issue\s*Date|DOI|Date\s*of\s*Issue|Issued)\s*[:\-]?\s*(?:Validity[^\n]*\n\s*)?(\d{1,2}[\/\-\.:]\d{1,2}[\/\-\.:]\d{2,4})",
        r"(?:Issue\s*Date|DOI|Date\s*of\s*Issue)\s*[:\-]?\s*(\d{1,2}[\/\-\.:]\d{1,2}[\/\-\.:]\d{2,4})",
    ])
    # Normalize colon-separated dates to slash-separated
    if doi:
        doi = doi.replace(":", "/")

    # --- Validity / Expiry ---
    # OCR produces dates like 12°07'2044 or 12:07:2044
    # First find all date-like patterns including mangled ones
    all_dates = re.findall(r"\b(\d{1,2})[\/\-\.:'°](\d{1,2})[\/\-\.:'°](\d{4})\b", text)
    parsed_dates = [f"{d}/{m}/{y}" for d, m, y in all_dates]

    doe = None
    if not doi:
        # Try to find issue date from parsed dates
        for d in parsed_dates:
            year = d.split("/")[-1]
            try:
                if 2020 <= int(year) <= 2030:
                    doi = d
                    break
            except ValueError:
                pass

    # Find expiry: look for future date > 2030
    for d in parsed_dates:
        year = d.split("/")[-1]
        try:
            if int(year) > 2030 and d != dob:
                doe = d
                break
        except ValueError:
            pass

    # --- Blood Group ---
    blood_group = find_first([
        r"Blood\s*Group\s*[:\-\.;]?\s*([ABO]{1,2}[+-]?)",
    ])

    # --- Guardian / Parent ---
    # OCR produces: "Son/Daughter Wite of : POOJARI SUDHAKAR" or "Son/Daughter'Wite of -POOJAR! SUDHAKAR"
    guardian = find_first([
        r"(?:Son|Daughter|Wife|Wite|Wile|S/O|D/O|W/O|Son/Daughter['\s]*(?:Wife|Wite|Wile)\s*(?:of|ot))\s*[:\-]?\s*([A-Z!][A-Z!\s]{3,40}?)(?=\s*[:\d]|\n|$|Address)",
    ])
    if guardian:
        guardian = guardian.replace("!", "")
        guardian = re.sub(r"\s+(ae|aides|SS|SJ|wer|var|\d)\s*$", "", guardian, flags=re.IGNORECASE).strip()
        guardian = " ".join(guardian.split())

    # --- Address ---
    address = find_first([
        r"Address\s*[:\-]?\s*\n?\s*(.+(?:\n.+){0,3}?)(?=\n\s*$|\nDate of|$)",
    ])

    # --- Issuing Authority ---
    issuing_auth = find_first([
        r"(?:Issued\s*by|Issuing\s*Authority)\s*[:\-]?\s*([A-Za-z\s]+?)(?=\n|$)"
    ])
    if not issuing_auth:
        issuing_auth = "Transport Department / Licensing Authority"

    # --- Gender ---
    gender = find_first([
        r"\b(?:Sex|Gender)\s*[:\-]?\s*([MF])\b"
    ])

    # Completeness scoring
    fields = [dl_number, full_name, dob, doi, doe, guardian]
    valid_count = sum(1 for f in fields if f)
    conf_score = round((valid_count / len(fields)) * 100.0, 2)
    conf_level = "HIGH" if conf_score >= 75 else ("MEDIUM" if conf_score >= 50 else "LOW")

    # Normalized ISO Dates
    dob_iso = normalize_date_iso(dob)
    doi_iso = normalize_date_iso(doi)
    doe_iso = normalize_date_iso(doe)

    return {
        "document_type": "DRIVING_LICENSE",
        "status": "PROCESSED",
        "identity": {
            "full_name": full_name,
            "surname": full_name.split()[-1] if full_name and len(full_name.split()) > 1 else None,
            "given_name": " ".join(full_name.split()[:-1]) if full_name and len(full_name.split()) > 1 else full_name,
            "nationality": "IND",
            "date_of_birth": dob_iso,
            "gender": normalize_gender(gender)
        },
        "document": {
            "document_number": dl_number,
            "date_of_issue": doi_iso,
            "date_of_expiry": doe_iso,
            "place_of_birth": None,
            "issuing_authority": issuing_auth
        },
        "additional_information": {
            "license_number": dl_number,
            "guardian_name": guardian,
            "blood_group": blood_group,
            "address": address
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
