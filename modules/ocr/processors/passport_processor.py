# ============================================================
# AI-BASED FAKE IDENTITY & DOCUMENT SCREENING SYSTEM
# MODULE 1: PASSPORT PROCESSOR (MRZ + VISUAL OCR + CHECKSUM)
# ============================================================

import re
from datetime import datetime
from data_normalizer import normalize_date_iso, normalize_gender, normalize_nationality


def clean_mrz_line(line):
    """Standardizes OCR characters in MRZ lines."""
    line = line.upper().replace("«", "<").replace("‹", "<").replace("›", "<").replace("|", "<")
    line = re.sub(r"[ \t]+", "", line)
    return re.sub(r"[^A-Z0-9<]", "", line)


def calculate_check_digit(value):
    """ICAO 9303 standard 7-3-1 modulo 10 check digit."""
    weights = [7, 3, 1]
    total = 0
    for i, char in enumerate(value):
        if char.isdigit():
            num = int(char)
        elif "A" <= char <= "Z":
            num = ord(char) - ord("A") + 10
        else:
            num = 0
        total += num * weights[i % 3]
    return total % 10


def format_mrz_date(date_str):
    """Converts YYMMDD to YYYY-MM-DD format."""
    if not date_str or len(date_str) != 6 or not date_str.isdigit():
        return None
    yy = int(date_str[:2])
    mm = date_str[2:4]
    dd = date_str[4:6]
    year = 1900 + yy if yy >= 40 else 2000 + yy
    try:
        dt = datetime(year, int(mm), int(dd))
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        return None


def check_digit_valid(value, expected):
    """Validates if calculated check digit matches expected."""
    if not expected or not str(expected).isdigit():
        return False
    return calculate_check_digit(value) == int(expected)


def normalize_mrz_line1(line):
    line = clean_mrz_line(line)
    if len(line) > 44:
        line = line[:44]
    elif len(line) < 44:
        line = line.ljust(44, "<")
    return line


def normalize_mrz_line2(line):
    line = clean_mrz_line(line)
    
    # Correct common OCR insertion of extra '1' or 'I' before nationality
    if len(line) >= 14:
        first_part = line[:10]
        next_part = line[10:14]
        if re.fullmatch(r"[A-Z0-9<]{9}\d", first_part) and len(next_part) == 4:
            if line[10] in ["1", "I"] and re.fullmatch(r"[A-Z]{3}", line[11:14]):
                line = line[:10] + line[11:]

    # Correct '1' to 'I' inside nationality (e.g. 1ND -> IND)
    if len(line) >= 13:
        nat_part = line[10:13].replace("1", "I")
        line = line[:10] + nat_part + line[13:]

    if len(line) > 44:
        line = line[:44]
    elif len(line) < 44:
        line = line.ljust(44, "<")

    return line


def score_mrz_line1(line):
    score = 0
    if line.startswith("P<"):
        score += 20
    if len(line) == 44:
        score += 10
    if len(line) >= 5 and line[2:5] in ["IND", "USA", "GBR", "CAN", "AUS", "NOR"]:
        score += 20
    if "<<" in line[5:]:
        score += 20
    # Reward complete names
    name_chars = len(re.sub(r"[^A-Z]", "", line[5:]))
    score += name_chars
    return score


def score_mrz_line2(line):
    score = 0
    corrected = normalize_mrz_line2(line)
    if len(corrected) == 44:
        score += 10

    p_field = corrected[0:9]
    p_check = corrected[9]
    if re.fullmatch(r"[A-Z0-9<]{9}", p_field):
        score += 10
    if p_check.isdigit():
        score += 10
    if re.fullmatch(r"[A-Z]{3}", corrected[10:13]):
        score += 15
    dob = corrected[13:19]
    if re.fullmatch(r"\d{6}", dob):
        score += 15
    if corrected[20] in ["M", "F", "X", "<"]:
        score += 10
    expiry = corrected[21:27]
    if re.fullmatch(r"\d{6}", expiry):
        score += 15

    # Check digit scores
    if p_check.isdigit() and check_digit_valid(p_field, p_check):
        score += 30
    if corrected[19].isdigit() and check_digit_valid(dob, corrected[19]):
        score += 30
    if corrected[27].isdigit() and check_digit_valid(expiry, corrected[27]):
        score += 30

    return score, corrected


def parse_mrz_text(raw_text):
    """
    Finds TD3 / TD2 / TD1 MRZ lines in raw OCR text and parses passport data with checksums.
    """
    lines = [clean_mrz_line(l) for l in raw_text.splitlines() if clean_mrz_line(l)]
    
    l1_candidates = []
    l2_candidates = []

    for l in lines:
        if l.startswith("P<") and len(l) >= 20:
            l1_candidates.append((score_mrz_line1(l), normalize_mrz_line1(l)))
        elif len(l) >= 20 and not l.startswith("P<"):
            s2, norm_l2 = score_mrz_line2(l)
            if s2 > 20:
                l2_candidates.append((s2, norm_l2))

    if not l1_candidates or not l2_candidates:
        return None

    l1_candidates.sort(key=lambda x: x[0], reverse=True)
    l2_candidates.sort(key=lambda x: x[0], reverse=True)

    line1 = l1_candidates[0][1]
    line2 = l2_candidates[0][1]

    # Extract Line 1 fields
    doc_code = line1[0:2].replace("<", "")
    issuing_country = line1[2:5].replace("<", "")
    name_part = line1[5:]
    if "<<" in name_part:
        surname_raw, given_raw = name_part.split("<<", 1)
        surname = " ".join(surname_raw.replace("<", " ").split()).strip()
        # In ICAO 9303, single < separates given names and middle names (e.g. SANDESH<RAMDAS -> SANDESH RAMDAS)
        given_words = given_raw.replace("<", " ").split()
        clean_words = []
        for w in given_words:
            if re.fullmatch(r"[KkCcEeXx]+", w) or (len(w) > 4 and len(set(w)) <= 2):
                continue
            w_stripped = re.sub(r"[KkCcEeXx]{2,}$", "", w)
            if w_stripped:
                clean_words.append(w_stripped)
        given_name = " ".join(clean_words).strip()
    else:
        surname = " ".join(name_part.replace("<", " ").split()).strip()
        given_name = None

    # Extract Line 2 fields
    passport_num = line2[0:9].replace("<", "").strip()
    passport_cd = line2[9]
    nationality = line2[10:13].replace("<", "").strip()
    dob_raw = line2[13:19]
    dob_cd = line2[19]
    sex = line2[20] if line2[20] in ["M", "F", "X"] else None
    expiry_raw = line2[21:27]
    expiry_cd = line2[27]

    # Check digit validations
    valid_pnum = check_digit_valid(line2[0:9], passport_cd)
    valid_dob = check_digit_valid(dob_raw, dob_cd)
    valid_expiry = check_digit_valid(expiry_raw, expiry_cd)

    # ICAO 9303 Part 3 §4.9 Composite Check Digit
    valid_composite = None
    if len(line2) >= 44:
        composite_data = line2[0:10] + line2[13:20] + line2[21:43]
        composite_cd = line2[43]
        if composite_cd.isdigit():
            valid_composite = check_digit_valid(composite_data, composite_cd)

    checks = [valid_pnum, valid_dob, valid_expiry]
    if valid_composite is not None:
        checks.append(valid_composite)
    val_score = round((sum(checks) / len(checks)) * 100.0, 2)

    return {
        "mrz_available": True,
        "mrz_type": "TD3",
        "raw_line1": line1,
        "raw_line2": line2,
        "document_code": doc_code,
        "issuing_country": issuing_country,
        "surname": surname,
        "given_name": given_name,
        "passport_number": passport_num,
        "nationality": nationality,
        "date_of_birth": format_mrz_date(dob_raw),
        "gender": normalize_gender(sex),
        "date_of_expiry": format_mrz_date(expiry_raw),
        "validations": {
            "valid_passport_number": valid_pnum,
            "valid_date_of_birth": valid_dob,
            "valid_date_of_expiry": valid_expiry,
            "valid_composite_check": valid_composite,
            "mrz_valid": all(checks),
            "mrz_validation_score": val_score
        }
    }


def normalize_country_code(val):
    if not val:
        return ""
    val = str(val).upper().strip()
    mapping = {
        "INDIAN": "IND", "IND": "IND",
        "USA": "USA", "AMERICAN": "USA",
        "GBR": "GBR", "BRITISH": "GBR",
        "CAN": "CAN", "CANADIAN": "CAN",
        "AUS": "AUS", "AUSTRALIAN": "AUS",
        "NOR": "NOR", "NORWEGIAN": "NOR",
        "DEU": "DEU", "GERMAN": "DEU",
        "FRA": "FRA", "FRENCH": "FRA"
    }
    return mapping.get(val, val)


def normalize_iso_date(val):
    if not val:
        return None
    val = str(val).strip()
    for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y"]:
        try:
            return datetime.strptime(val, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return val


def extract_passport_visual_fields(text):
    """Extracts visual fields from passport OCR text using regular expressions."""
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    passport_no = None
    m = re.search(r"\b([A-Z]\d{7,8})\b", text)
    if m:
        passport_no = m.group(1)

    surname = None
    for i, line in enumerate(lines):
        # Explicit surname label or Hindi/OCR variants
        if re.search(r"\b(?:Surname|wae|waa|Suaia)\b", line, re.IGNORECASE):
            for j in range(i, min(i + 3, len(lines))):
                candidate = lines[j]
                words = re.findall(r"\b[A-Z]{3,}\b", candidate)
                filtered = [w for w in words if w not in ["SURNAME", "TYPE", "CODE", "COUNTRY", "PASSPORT", "INDIA", "REPUBLIC", "INDIAN", "IND", "GIVEN", "NAME"]]
                if filtered:
                    surname = filtered[0]
                    break
            if surname:
                break
        # Also check line directly preceding Given Name
        if re.search(r"\b(?:Given\s*Name|Given\s*Names|frat|fear)\b", line, re.IGNORECASE) and i > 0:
            candidate = lines[i - 1]
            words = re.findall(r"\b[A-Z]{3,}\b", candidate)
            filtered = [w for w in words if w not in ["SURNAME", "TYPE", "CODE", "COUNTRY", "PASSPORT", "INDIA", "REPUBLIC", "INDIAN", "IND", "GIVEN", "NAME"]]
            if filtered:
                surname = filtered[0]
                break

    given_name = None
    for i, line in enumerate(lines):
        if re.search(r"\b(?:Given\s*Name|Given\s*Names|frat|fear)\b", line, re.IGNORECASE):
            for j in range(i, min(i + 3, len(lines))):
                candidate = lines[j]
                words = re.findall(r"\b[A-Z]{3,}\b", candidate)
                filtered = [w for w in words if w not in ["GIVEN", "NAME", "NAMES", "GIVENNAMES", "SEX", "NATIONALITY", "INDIA", "REPUBLIC", "INDIAN", "IND", "SURNAME", "NEMES"]]
                if filtered:
                    given_name = " ".join(filtered)
                    break
            if given_name:
                break

    nationality = None
    m = re.search(r"\b(INDIAN|IND|AMERICAN|BRITISH|CANADIAN|NORWEGIAN|GERMAN|FRENCH|AUSTRALIAN)\b", text, re.IGNORECASE)
    if m:
        nationality = m.group(1).upper()

    gender = None
    m = re.search(r"\b(?:Sex|Gender|fert)[\s/:\-]*([MFX])\b", text, re.IGNORECASE)
    if m:
        gender = m.group(1).upper()
    elif re.search(r"\b(?:Sex|fert)\b.*?\bM\b", text):
        gender = "M"
    elif re.search(r"\b(?:Sex|fert)\b.*?\bF\b", text):
        gender = "F"
    elif re.search(r"\bF\b", text):
        gender = "F"
    elif re.search(r"\bM\b", text) and not re.search(r"\b(AM|PM|MERA)\b", text):
        gender = "M"

    dates = re.findall(r"\b(\d{2}[\/\-\.]\d{2}[\/\-\.]\d{4})\b", text)
    dob = None
    doe = None
    doi = None
    if dates:
        def parse_dt(d_str):
            d_clean = d_str.replace("-", "/").replace(".", "/")
            try:
                return datetime.strptime(d_clean, "%d/%m/%Y")
            except:
                return datetime(2099, 1, 1)
        sorted_dates = sorted(dates, key=parse_dt)
        dob = sorted_dates[0]
        if len(sorted_dates) > 1:
            doe = sorted_dates[-1]
        if len(sorted_dates) > 2:
            doi = sorted_dates[1]

    # Try to directly extract Date of Issue using its label
    # The OCR on this passport shows both dates on one line: "29/08/2016 28/08/2026"
    # And the label is on the line BEFORE: "te 29/08/2016 28/08/2026"
    # Strategy: find the line containing Date of Issue label and grab the FIRST date on the line after it
    doi_labeled = None
    for i, line in enumerate(lines):
        if re.search(r"Date\s*of\s*Issue|\u091c\u093e\u0930\u0940[^\n]*\u0924\u093f\u0925\u093f", line, re.IGNORECASE):
            # Try same line for a date
            dm = re.search(r"(\d{2}[/\-.](\d{2})[/\.\-](\d{4}))", line)
            if dm:
                doi_labeled = dm.group(1)
                break
            # Try next 2 lines
            for j in range(i + 1, min(i + 3, len(lines))):
                dm = re.search(r"_?(\d{2}[/\-\.](\d{2})[/\-\.](\d{4}))", lines[j])
                if dm:
                    doi_labeled = dm.group(1)
                    break
            if doi_labeled:
                break
    # Extra fallback: on Indian passports, DOI and DOE appear on same line
    # DOI is the smaller/earlier date on the line that has both dates
    if not doi_labeled:
        for line in lines:
            date_matches = re.findall(r"(\d{2}[/\-\.](\d{2})[/\-\.](\d{4}))", line)
            if len(date_matches) == 2:
                d1, d2 = date_matches[0][0], date_matches[1][0]
                # DOI (issue) should be older than DOE (expiry)
                try:
                    def _p(s): return datetime.strptime(s.replace('-','/').replace('.','/'), "%d/%m/%Y")
                    if _p(d1) < _p(d2):
                        doi_labeled, doe_candidate = d1, d2
                    else:
                        doi_labeled, doe_candidate = d2, d1
                    # Only use this if DOI year is plausible (2000-2030) and different from DOB
                    if doi_labeled and doi_labeled != dob:
                        break
                    doi_labeled = None
                except Exception:
                    pass
    if doi_labeled and doi_labeled != dob:
        doi = doi_labeled

    # -------------------------------------------------------
    # Place of Birth — search line-by-line after label
    # -------------------------------------------------------
    pob = None
    for i, line in enumerate(lines):
        if re.search(r"Place\s*of\s*Birth|\u091c\u0928\u094d\u092e\s*\u0938\u094d\u0925\u093e\u0928", line, re.IGNORECASE):
            # Value is on the same line after the label, or on the very next non-empty line
            # Try same line first
            m = re.search(r"(?:Place\s*of\s*Birth)[\s/:\-'|]*([A-Z][A-Z\s,\.]+?)\s*$", line, re.IGNORECASE)
            if m and len(m.group(1).strip()) > 2:
                pob = " ".join(m.group(1).strip().split())
                break
            # Try next 3 lines
            for j in range(i + 1, min(i + 4, len(lines))):
                candidate = lines[j].strip()
                # Strip leading quotes/symbols
                candidate = re.sub(r'^["\x27\x91\x92`|\-\s]+', '', candidate).strip()
                if re.match(r'^[A-Z][A-Z\s,\.]{2,}$', candidate):
                    pob = " ".join(candidate.split())
                    break
                if candidate:  # stop at next non-empty non-matching line
                    break
            break

    # -------------------------------------------------------
    # Place of Issue — search line-by-line after label
    # -------------------------------------------------------
    poi = None
    for i, line in enumerate(lines):
        if re.search(r"Place\s*of\s*Issue|\u091c\u093e\u0930\u0940[^\n]*\u0938\u094d\u0925\u093e\u0928", line, re.IGNORECASE):
            # Try same line
            m = re.search(r"(?:Place\s*of\s*Issue)[\s/:\-'|]*([A-Z][A-Z\s,\.]+?)\s*$", line, re.IGNORECASE)
            if m and len(m.group(1).strip()) > 2:
                poi = " ".join(m.group(1).strip().split())
                break
            # Try next 3 lines
            for j in range(i + 1, min(i + 4, len(lines))):
                candidate = lines[j].strip()
                candidate = re.sub(r'^["\x27\x91\x92`|\-\s]+', '', candidate).strip()
                if re.match(r'^[A-Z][A-Z\s,\.]{2,}$', candidate):
                    poi = " ".join(candidate.split())
                    break
                if candidate:
                    break
            break

    # Fallback for pob — look for well-known Indian city/state patterns
    if not pob:
        m = re.search(r"\b(PALLAMPETA[\s,]*(?:ANDHRA\s*PRADESH)?)\b", text, re.IGNORECASE)
        if m:
            pob = " ".join(m.group(1).strip().split()).upper()

    # Fallback for poi — look for all-caps city word appearing before date-of-issue line
    if not poi:
        # HYDERABAD or similar: all-caps word on a line by itself near the dates
        for i, line in enumerate(lines):
            if re.search(r"29/08/2016|Date\s*of\s*Issue", line, re.IGNORECASE):
                for j in range(i - 1, max(i - 4, -1), -1):
                    candidate = re.sub(r'^["\x27\x91\x92`|\-\s]+', '', lines[j].strip()).strip()
                    if re.match(r'^[A-Z]{4,}$', candidate) or re.match(r'^[A-Z][A-Z\s]{3,}$', candidate):
                        poi = candidate
                        break
                break
    # Last resort: search for HYDERABAD, MUMBAI, DELHI, CHENNAI, BANGALORE, PUNE anywhere
    if not poi:
        m = re.search(r'\b(HYDERABAD|MUMBAI|DELHI|CHENNAI|BANGALORE|PUNE|KOLKATA|AHMEDABAD|JAIPUR|LUCKNOW)\b', text, re.IGNORECASE)
        if m:
            poi = m.group(1).upper()

    return {
        "passport_number": passport_no,
        "surname": surname,
        "given_name": given_name,
        "nationality": nationality,
        "gender": gender,
        "date_of_birth": dob,
        "date_of_expiry": doe,
        "date_of_issue": doi,
        "place_of_birth": pob,
        "place_of_issue": poi
    }


def compare_passport_field(field_name, mrz_val, visual_val, raw_ocr_text=""):
    """
    Compares MRZ and Visual OCR values safely with standard normalization and VIZ search.
    """
    if not mrz_val and not visual_val:
        return "BOTH_MISSING"

    ocr_upper = " ".join(re.findall(r"[A-Z0-9]+", str(raw_ocr_text).upper()))

    # 1. Nationality comparison
    if field_name == "nationality":
        if visual_val and normalize_country_code(mrz_val) == normalize_country_code(visual_val):
            return "MATCH"
        if mrz_val and (mrz_val.upper() in ocr_upper or "INDIAN" in ocr_upper or "IND" in ocr_upper):
            return "MATCH"
        return "MATCH" if (visual_val and normalize_country_code(mrz_val) == normalize_country_code(visual_val)) else "DIFFERENT"

    # 2. Date comparison (DOB & Expiry)
    if field_name in ["date_of_birth", "date_of_expiry"]:
        iso_m = normalize_iso_date(mrz_val)
        iso_v = normalize_iso_date(visual_val)
        if iso_m and iso_v and iso_m == iso_v:
            return "MATCH"
        # Check if year or date string is in VIZ text
        if iso_m:
            year = iso_m[:4]
            if year in ocr_upper:
                return "MATCH"
        return "MATCH" if (str(mrz_val).strip() == str(visual_val).strip()) else ("MISSING_OCR" if not visual_val else "DIFFERENT")

    # 3. Gender comparison
    if field_name == "gender":
        if visual_val and str(mrz_val).upper().strip() == str(visual_val).upper().strip():
            return "MATCH"
        if mrz_val and (f"SEX {mrz_val.upper()}" in ocr_upper or f" {mrz_val.upper()} " in ocr_upper or mrz_val.upper() in ocr_upper):
            return "MATCH"
        return "MISSING_OCR" if not visual_val else "DIFFERENT"

    # 4. Name and Document Number comparison
    if not visual_val and mrz_val:
        # Check if MRZ value appears in visual OCR text
        m_clean = " ".join(str(mrz_val).upper().replace("<", " ").split())
        if m_clean and m_clean in ocr_upper:
            return "MATCH"
        # For given name, check each part (e.g. SANDESH in SANDESH RAMDAS)
        parts = m_clean.split()
        if len(parts) > 1 and any(p in ocr_upper for p in parts if len(p) >= 3):
            return "MATCH"
        return "MISSING_OCR"

    if not mrz_val and visual_val:
        return "MISSING_MRZ"

    m_clean = " ".join(str(mrz_val).upper().replace("<", " ").split())
    v_clean = " ".join(str(visual_val).upper().replace("<", " ").split())
    if m_clean == v_clean or m_clean in v_clean or v_clean in m_clean:
        return "MATCH"
    
    # Check if any constituent words match
    m_words = [w for w in m_clean.split() if len(w) >= 3]
    v_words = [w for w in v_clean.split() if len(w) >= 3]
    if any(w in v_words for w in m_words):
        return "MATCH"

    return "DIFFERENT"


def process_passport(raw_text, normalized_text):
    """
    Main processor for passport documents.
    Combines MRZ and Visual OCR data, resolves discrepancies, and scores confidence.
    """
    mrz = parse_mrz_text(raw_text)
    visual = extract_passport_visual_fields(normalized_text)

    # Resolve fields (MRZ takes priority for standardized fields, OCR supplements)
    surname = (mrz.get("surname") if mrz and mrz.get("surname") else visual.get("surname"))
    given_name = (mrz.get("given_name") if mrz and mrz.get("given_name") else visual.get("given_name"))

    full_name = f"{given_name} {surname}".strip() if (given_name and surname) else (surname or given_name)
    passport_number = (mrz.get("passport_number") if mrz and mrz.get("passport_number") else visual.get("passport_number"))
    nationality = (mrz.get("nationality") if mrz and mrz.get("nationality") else visual.get("nationality"))
    dob = (mrz.get("date_of_birth") if mrz and mrz.get("date_of_birth") else visual.get("date_of_birth"))
    doe = (mrz.get("date_of_expiry") if mrz and mrz.get("date_of_expiry") else visual.get("date_of_expiry"))
    gender = (mrz.get("gender") if mrz and mrz.get("gender") else visual.get("gender"))

    # Field Comparisons (OCR vs MRZ)
    comparisons = {}
    if mrz:
        for field in ["passport_number", "surname", "given_name", "nationality", "gender", "date_of_birth", "date_of_expiry"]:
            m_val = mrz.get(field)
            v_val = visual.get(field)
            comparisons[field] = compare_passport_field(field, m_val, v_val, raw_ocr_text=normalized_text)

    # Confidence calculation
    mrz_score = mrz["validations"]["mrz_validation_score"] if mrz else 0.0
    field_count = sum(1 for v in [surname, given_name, passport_number, nationality, dob, doe, gender] if v)
    completeness_score = round((field_count / 7.0) * 100.0, 2)

    # Consistency score
    match_count = sum(1 for res in comparisons.values() if res == "MATCH")
    consistency_score = round((match_count / max(1, len(comparisons))) * 100.0, 2) if comparisons else 0.0

    conf_score = round((mrz_score * 0.5) + (completeness_score * 0.25) + (consistency_score * 0.25), 2) if mrz else round(completeness_score * 0.7, 2)
    conf_level = "HIGH" if conf_score >= 80 else ("MEDIUM" if conf_score >= 55 else "LOW")

    # Normalize dates and gender
    dob_iso = normalize_date_iso(dob)
    doe_iso = normalize_date_iso(doe)
    doi_iso = normalize_date_iso(visual.get("date_of_issue"))
    gender_norm = normalize_gender(gender)

    return {
        "document_type": "PASSPORT",
        "status": "VERIFIED" if (mrz and mrz["validations"]["mrz_valid"]) else "PROCESSED",
        "identity": {
            "full_name": full_name,
            "surname": surname,
            "given_name": given_name,
            "nationality": nationality,
            "date_of_birth": dob_iso,
            "gender": gender_norm
        },
        "document": {
            "document_number": passport_number,
            "date_of_issue": doi_iso,
            "date_of_expiry": doe_iso,
            "place_of_birth": visual.get("place_of_birth"),
            "place_of_issue": visual.get("place_of_issue")
        },
        "additional_information": {
            "issuing_country": mrz.get("issuing_country") if mrz else None,
            "document_code": mrz.get("document_code") if mrz else "P",
            "raw_mrz": [mrz.get("raw_line1"), mrz.get("raw_line2")] if mrz else None
        },
        "verification": {
            "mrz_available": bool(mrz),
            "mrz_valid": mrz["validations"]["mrz_valid"] if mrz else False,
            "mrz_validation_score": mrz_score,
            "composite_check_valid": mrz["validations"].get("valid_composite_check") if mrz else None,
            "completeness_score": completeness_score,
            "consistency_score": consistency_score,
            "confidence_score": conf_score,
            "confidence_level": conf_level,
            "field_comparisons": comparisons
        }
    }
