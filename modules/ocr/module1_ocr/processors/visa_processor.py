# ============================================================
# AI-BASED FAKE IDENTITY & DOCUMENT SCREENING SYSTEM
# MODULE 1: VISA PROCESSOR
# ============================================================

import re
from data_normalizer import normalize_date_iso, normalize_gender, normalize_nationality, normalize_country_code


def process_visa(raw_text, normalized_text):
    """
    Extracts structured fields from Visa travel documents.
    Covers standard Schengen, US, UK, Indian, and International Visas.
    """
    text = normalized_text

    def find_match(patterns):
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                return " ".join(m.group(1).strip().split())
        return None

    # Visa / Document Number
    visa_number = find_match([
        r"Visa\s*(?:No|Number)\s*[:\-]?\s*([A-Z0-9]{8,14})",
        r"Control\s*Number\s*[:\-]?\s*([A-Z0-9]{8,14})",
        r"\b([A-Z]\d{7,9})\b",
        r"\b(\d{9,14})\b"
    ])

    # Visa Type / Category
    visa_type = find_match([
        r"Visa\s*(?:Type|Class|Category)\s*[/:]?\s*([A-Z0-9\/\-]+)",
        r"(?:Type\s*de\s*visa|Type\s*of\s*Visa|Type)\s*[/:]?\s*([A-Z0-9\/\-]+)",
        r"\bType\s*[:\-]?\s*([A-Z0-9]+)\b"
    ])

    # Issuing Authority / Post
    issuing_post = find_match([
        r"(?:Issuing\s*Post|Place\s*of\s*Issue|Delivre\s*a|Délivré\s*à|Authority)\s*[:\-]?\s*([A-Z\s]+?)(?=\n|Surname|Given|Du|From|$)",
        r"\b(PARIS|LONDON|NEW YORK|BERLIN|DELHI|MUMBAI|WASHINGTON)\b"
    ])

    # Passport Number on Visa
    passport_number = find_match([
        r"(?:Passport\s*(?:No|Number)|PPT\s*(?:No)?|Numéro\s*de\s*passeport)\s*[:\-]?\s*([A-Z0-9]{7,12})",
        r"\b([A-Z]\d{7,8})\b"
    ])

    # Applicant Name
    surname = find_match([
        r"(?:Surname|Nom|Last\s*Name)\s*[:\-]?\s*([A-Z\s]+?)(?=\n|Given|First|Prénom|$)"
    ])

    given_name = find_match([
        r"(?:Given\s*Name[s]?|Prénom[s]?|First\s*Name)\s*[:\-]?\s*([A-Z\s]+?)(?=\n|Sex|Sexe|Date|$)"
    ])

    # Full name extraction fallback
    if not surname and not given_name:
        name_cand = find_match([
            r"(?:Name|Nom\s*et\s*prénom)\s*[:\-]?\s*([A-Z\s]+?)(?=\n|Passport|DOB|$)",
            r"\b([A-Z]{3,}\s+[A-Z]{3,})\b"
        ])
        if name_cand:
            parts = name_cand.split()
            surname = parts[-1]
            given_name = " ".join(parts[:-1]) if len(parts) > 1 else name_cand

    full_name = f"{given_name} {surname}".strip() if (given_name and surname) else (surname or given_name)

    # Nationality
    nationality = find_match([
        r"(?:Nationality|Nationalité)\s*[:\-]?\s*([A-Z]+)"
    ])
    if nationality:
        nationality = normalize_country_code(nationality)

    # Gender
    gender = find_match([
        r"\b(?:Sex|Gender|Sexe)\s*[:\-]?\s*([MFX])\b"
    ])

    # Date of Birth
    dob = find_match([
        r"(?:Birth\s*Date|Date\s*of\s*Birth|DOB|Date\s*de\s*naissance)\s*[:\-]?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}|[0-9A-Z]{7,11})"
    ])

    # Date of Issue / Valid From
    doi = find_match([
        r"(?:Issue\s*Date|Date\s*of\s*Issue|Délivré\s*le|Delivre\s*le|Valid\s*From|Du|From)\s*[:\-]?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}|[0-9]{1,2}[A-Z]{3}[0-9]{2,4})"
    ])

    valid_from = doi  # Synonymous for visas unless distinct

    # Date of Expiry / Valid Until
    doe = find_match([
        r"(?:Expiration\s*Date|Expiry\s*Date|Valid\s*Until|Au|Until|Jusqu['\s]*au)\s*[:\-]?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}|[0-9]{1,2}[A-Z]{3}[0-9]{2,4})"
    ])

    valid_until = doe

    # Number of Entries
    entries = find_match([
        r"(?:Number\s*of\s*Entries|Nombre\s*d['\s]*entrées|Entries)\s*[:\-]?\s*([MULT0-9]+|MULTIPLE|SINGLE|01|02|M|S)",
        r"\b(MULT|MULTIPLE|SINGLE|01|02)\b"
    ])

    # Permitted Duration of Stay
    duration = find_match([
        r"(?:Duration\s*of\s*Stay|Durée\s*de\s*séjour|Stay\s*Duration|Duration)\s*[:\-]?\s*(\d+\s*(?:DAYS|JOURS|MONTHS|MOIS|WEEKS)?)",
        r"\b(\d{1,3}\s*DAYS)\b"
    ])

    # Normalized ISO Dates
    dob_iso = normalize_date_iso(dob)
    doi_iso = normalize_date_iso(doi)
    valid_from_iso = normalize_date_iso(valid_from)
    valid_until_iso = normalize_date_iso(valid_until)
    doe_iso = normalize_date_iso(doe)

    # Completeness score
    key_fields = [visa_number, visa_type, passport_number, surname, doi, doe]
    valid_count = sum(1 for f in key_fields if f)
    conf_score = round((valid_count / len(key_fields)) * 100.0, 2)
    conf_level = "HIGH" if conf_score >= 80 else ("MEDIUM" if conf_score >= 50 else "LOW")

    return {
        "document_type": "VISA",
        "status": "PROCESSED",
        "identity": {
            "full_name": full_name,
            "surname": surname,
            "given_name": given_name,
            "nationality": nationality,
            "date_of_birth": dob_iso,
            "gender": normalize_gender(gender)
        },
        "document": {
            "document_number": visa_number,
            "passport_number": passport_number,
            "visa_type": visa_type,
            "date_of_issue": doi_iso,
            "date_of_expiry": doe_iso,
            "valid_from": valid_from_iso,
            "valid_until": valid_until_iso,
            "number_of_entries": entries,
            "duration_of_stay": duration,
            "place_of_issue": issuing_post,
            "issuing_authority": issuing_post
        },
        "additional_information": {
            "visa_number": visa_number,
            "visa_type": visa_type,
            "number_of_entries": entries,
            "duration_of_stay": duration,
            "issuing_post": issuing_post,
            "barcode_or_qr_data": None
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

