# ============================================================
# AI-BASED FAKE IDENTITY & DOCUMENT SCREENING SYSTEM
# MODULE 1: NATIONAL ID PROCESSOR (AADHAAR / CITIZEN ID)
# ============================================================

import re
from data_normalizer import normalize_date_iso, normalize_gender


def process_national_id(raw_text, normalized_text):
    """
    Extracts structured fields from National ID / Aadhaar documents.
    """
    text = normalized_text

    def find_match(patterns):
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                return " ".join(m.group(1).strip().split())
        return None

    # Aadhaar 12-digit number (e.g. 1234 5678 9012)
    id_number = find_match([
        r"\b(\d{4}\s\d{4}\s\d{4})\b",
        r"\b(\d{12})\b",
        r"(?:ID|Aadhaar|Card)\s*(?:No|Number)?\s*[:\-]?\s*([A-Z0-9\s]{8,16})"
    ])

    if id_number and len(id_number.replace(" ", "")) == 12:
        digits = id_number.replace(" ", "")
        id_number = f"{digits[:4]} {digits[4:8]} {digits[8:]}"

    # -------------------------------------------------------
    # Smart Name Extraction for Aadhaar
    # The card has:  Telugu line (garbage) → English Name line → S/O line
    # Strategy:
    #   1. Find English Title Case name line that appears right before
    #      a "S/O" or "D/O" or "W/O" line.
    #   2. Fallback: find any clean Title Case line appearing after "To"
    #      that is not an address/label line.
    # -------------------------------------------------------
    full_name = None
    lines = text.splitlines()

    # Strategy 1: Find line immediately before S/O / D/O / W/O line
    for i, line in enumerate(lines):
        stripped = line.strip()
        if re.match(r"^[SDWF][/\\][ODWF]\s+", stripped, re.IGNORECASE) or \
           re.match(r"^(?:Son|Daughter|Wife|Father|Mother)\s*[/\\]?[Oo]", stripped):
            # The real name is on the previous non-empty line
            for j in range(i - 1, max(i - 4, -1), -1):
                candidate = lines[j].strip()
                # Must be clean ASCII Title Case: e.g. "Panuganti Varshith Goud"
                if candidate and \
                   re.match(r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,4}$', candidate) and \
                   len(candidate) > 4:
                    full_name = candidate
                    break
            if full_name:
                break

    # Strategy 2: After a "To" label, find first clean Title Case line
    if not full_name:
        found_to = False
        for line in lines:
            stripped = line.strip()
            if stripped.lower() == "to":
                found_to = True
                continue
            if found_to:
                if re.match(r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,4}$', stripped) and len(stripped) > 4:
                    full_name = stripped
                    break
                # Stop searching after a few lines if we hit an address label
                if re.search(r'\b(S/O|D/O|W/O|Address|VTC|PIN|Mobile|District|State)\b', stripped, re.IGNORECASE):
                    break

    # Strategy 3: DOB line context — look for name on the line just before DOB
    if not full_name:
        for i, line in enumerate(lines):
            if re.search(r'DOB|Date\s*of\s*Birth', line, re.IGNORECASE):
                for j in range(i - 1, max(i - 4, -1), -1):
                    candidate = lines[j].strip()
                    if re.match(r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,4}$', candidate) and len(candidate) > 4:
                        full_name = candidate
                        break
                break

    # Strategy 4: Broadest fallback — any clean mixed-case name-like line
    if not full_name:
        for line in lines:
            stripped = line.strip()
            if re.match(r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,4}$', stripped) and \
               not re.search(r'\b(India|Aadhaar|Authority|Identification|Government|Verification|citizenship|scanning)\b', stripped) and \
               len(stripped) > 5:
                full_name = stripped
                break

    # -------------------------------------------------------
    # Date of Birth — look for DOB label or SA/DOB pattern
    # -------------------------------------------------------
    dob = find_match([
        r"(?:SA/DOB|DOB|Date\s*of\s*Birth|/DOB)\s*[:\-]?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})",
        r"(?:Year\s*of\s*Birth|YOB)\s*[:\-]?\s*(\d{4})"
    ])

    # -------------------------------------------------------
    # Gender
    # -------------------------------------------------------
    gender = None
    if re.search(r"\b(?:FEMALE|WOMAN)\b", text, re.IGNORECASE):
        gender = "F"
    elif re.search(r"\b(?:MALE|MAN)\b", text, re.IGNORECASE):
        gender = "M"

    # -------------------------------------------------------
    # Guardian / Father name (S/O line)
    # -------------------------------------------------------
    guardian = find_match([
        r"(?:S/O|D/O|W/O|Son/Daughter[^\n]*of)\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})",
    ])

    # -------------------------------------------------------
    # Address
    # -------------------------------------------------------
    address_parts = []
    collecting = False
    for line in lines:
        stripped = line.strip()
        if re.match(r'^\d+-\d+', stripped) or re.search(r'\b(VTC|District|State|PIN|koheda|gandicheruvu|Hayathnagar|Rangareddi)\b', stripped, re.IGNORECASE):
            collecting = True
        if collecting:
            if stripped and not re.search(r'\b(Aadhaar|UIDAI|Your|Mobile|VID|Signature)\b', stripped, re.IGNORECASE):
                address_parts.append(stripped)
            if re.search(r'PIN\s*Code', stripped, re.IGNORECASE):
                collecting = False
    address = ", ".join(address_parts[:5]) if address_parts else None

    # -------------------------------------------------------
    # VID
    # -------------------------------------------------------
    vid = find_match([r"VID\s*[:\-]?\s*([\d\s]{19,23})"])
    if vid:
        vid = vid.replace(" ", "")
        vid = f"{vid[:4]} {vid[4:8]} {vid[8:12]} {vid[12:]}" if len(vid) == 16 else vid

    # Completeness scoring
    fields = [id_number, full_name, dob, gender]
    valid_count = sum(1 for f in fields if f)
    conf_score = round((valid_count / len(fields)) * 100.0, 2)
    conf_level = "HIGH" if conf_score >= 75 else ("MEDIUM" if conf_score >= 50 else "LOW")

    # Normalized ISO Dates
    dob_iso = normalize_date_iso(dob)

    return {
        "document_type": "NATIONAL_ID",
        "status": "PROCESSED",
        "identity": {
            "full_name": full_name,
            "surname": full_name.split()[-1] if full_name and len(full_name.split()) > 1 else None,
            "given_name": " ".join(full_name.split()[:-1]) if full_name and len(full_name.split()) > 1 else full_name,
            "nationality": "INDIAN" if ("AADHAAR" in text.upper() or "INDIA" in text.upper()) else None,
            "date_of_birth": dob_iso,
            "gender": normalize_gender(gender)
        },
        "document": {
            "document_number": id_number,
            "date_of_issue": None,
            "date_of_expiry": None,
            "place_of_birth": None,
            "issuing_authority": "Unique Identification Authority of India (UIDAI)" if "AADHAAR" in text.upper() else "National ID Authority"
        },
        "additional_information": {
            "id_number": id_number,
            "id_type": "Aadhaar Card" if "AADHAAR" in text.upper() else "National ID",
            "guardian_name": guardian,
            "address": address,
            "vid": vid
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
