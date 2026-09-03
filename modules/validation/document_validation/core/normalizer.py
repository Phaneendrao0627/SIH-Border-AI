"""
Safe normalization service for document data and dates.
"""
from dataclasses import dataclass
from datetime import date, datetime
import re
from typing import Optional, Union, Tuple

from document_validation.models.input_contract import ValidationInput


@dataclass
class NormalizedDates:
    dob: Optional[date] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    dob_raw_valid: bool = False
    issue_date_raw_valid: bool = False
    expiry_date_raw_valid: bool = False


@dataclass
class NormalizedInput:
    original: ValidationInput
    document_type: str
    country_code: str
    name: str
    document_number: str
    dates: NormalizedDates
    gender: Optional[str] = None
    visa_type: Optional[str] = None
    stay_days: Optional[int] = None
    mrz_lines: list = None


ACCEPTED_DATE_FORMATS = [
    "%Y-%m-%d",
    "%d-%m-%Y",
    "%Y/%m/%d",
    "%d/%m/%Y",
    "%d.%m.%Y",
    "%Y.%m.%d",
]


def parse_date_safe(date_str: Optional[str], pivot_year: int = 40) -> Tuple[Optional[date], bool]:
    """
    Parses a date string safely against accepted formats.
    Handles leap years, out-of-bounds days/months, and 6-digit YYMMDD MRZ dates.
    Returns (date_obj, is_valid_format).
    """
    if not date_str or not isinstance(date_str, str):
        return None, False

    clean_str = date_str.strip()
    if not clean_str:
        return None, False

    # Check 6-digit YYMMDD
    if re.match(r"^[0-9]{6}$", clean_str):
        yy = int(clean_str[0:2])
        mm = int(clean_str[2:4])
        dd = int(clean_str[4:6])
        century = 2000 if yy <= pivot_year else 1900
        full_year = century + yy
        try:
            parsed = date(full_year, mm, dd)
            return parsed, True
        except ValueError:
            return None, False

    for fmt in ACCEPTED_DATE_FORMATS:
        try:
            dt = datetime.strptime(clean_str, fmt)
            return dt.date(), True
        except ValueError:
            continue

    return None, False


def normalize_string(val: Optional[str]) -> str:
    """Strips leading/trailing whitespace and collapses internal multiple spaces."""
    if not val:
        return ""
    return re.sub(r"\s+", " ", val.strip())


def normalize_document_number(val: Optional[str]) -> str:
    """Removes hyphens and spaces, and converts to uppercase."""
    if not val:
        return ""
    return re.sub(r"[\s\-]+", "", val.strip().upper())


def parse_stay_duration(val: Optional[Union[int, str]]) -> Optional[int]:
    """Extracts number of days from integer or strings like '90 days', '30 days'."""
    if val is None:
        return None
    if isinstance(val, int):
        return val if val >= 0 else None
    if isinstance(val, str):
        match = re.search(r"(\d+)", val)
        if match:
            return int(match.group(1))
    return None


def normalize_input_data(inp: ValidationInput) -> NormalizedInput:
    """
    Produces a NormalizedInput object while preserving the original input intact.
    """
    clean_doc_type = normalize_string(inp.document_type).lower()
    clean_country = normalize_string(inp.country_code).upper()
    clean_name = normalize_string(inp.name).upper()
    clean_doc_num = normalize_document_number(inp.document_number)

    dob_obj, dob_ok = parse_date_safe(inp.date_of_birth)
    issue_obj, issue_ok = parse_date_safe(inp.date_of_issue)
    expiry_obj, expiry_ok = parse_date_safe(inp.date_of_expiry)

    dates = NormalizedDates(
        dob=dob_obj,
        issue_date=issue_obj,
        expiry_date=expiry_obj,
        dob_raw_valid=dob_ok if inp.date_of_birth else False,
        issue_date_raw_valid=issue_ok if inp.date_of_issue else True,
        expiry_date_raw_valid=expiry_ok if inp.date_of_expiry else True,
    )

    clean_gender = inp.gender.strip().upper() if inp.gender else None
    if clean_gender and clean_gender not in ["M", "F", "X", "MALE", "FEMALE"]:
        clean_gender = "UNKNOWN"
    elif clean_gender == "MALE":
        clean_gender = "M"
    elif clean_gender == "FEMALE":
        clean_gender = "F"

    stay_days = parse_stay_duration(inp.stay_duration)

    return NormalizedInput(
        original=inp,
        document_type=clean_doc_type,
        country_code=clean_country,
        name=clean_name,
        document_number=clean_doc_num,
        dates=dates,
        gender=clean_gender,
        visa_type=normalize_string(inp.visa_type) if inp.visa_type else None,
        stay_days=stay_days,
        mrz_lines=list(inp.mrz_lines)
    )
