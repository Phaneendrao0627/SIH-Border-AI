# ============================================================
# AI-BASED FAKE IDENTITY & DOCUMENT SCREENING SYSTEM
# MODULE 1: DATA NORMALIZER
# ============================================================

import re
from datetime import datetime


def normalize_date_iso(date_value):
    """
    Normalizes any date string into ISO 8601 format (YYYY-MM-DD).
    Handles formats:
      - DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY
      - YYYY-MM-DD, YYYY/MM/DD
      - DDMMMYYYY (e.g., 22MAY2023, 29AUG2016)
      - YYMMDD (MRZ 6-digit)
    """
    if not date_value:
        return None

    date_str = str(date_value).strip().upper()
    if not date_str or date_str in ["N/A", "NONE", "NULL"]:
        return None

    # Already ISO YYYY-MM-DD
    if re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        return date_str

    # Clean punctuation
    cleaned = re.sub(r"[^\w\/\-\.]", "", date_str)

    # 1. Check DD/MM/YYYY or DD-MM-YYYY or DD.MM.YYYY
    m = re.match(r"^(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{4})$", cleaned)
    if m:
        day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            return datetime(year, month, day).strftime("%Y-%m-%d")
        except ValueError:
            pass

    # 2. Check YYYY/MM/DD or YYYY.MM.DD
    m = re.match(r"^(\d{4})[\/\-\.](\d{1,2})[\/\-\.](\d{1,2})$", cleaned)
    if m:
        year, month, day = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            return datetime(year, month, day).strftime("%Y-%m-%d")
        except ValueError:
            pass

    # 3. Check text month formats (e.g. 22MAY2023, 22-MAY-2023, 22 MAY 2023)
    month_names = {
        "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
        "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12
    }
    m = re.search(r"(\d{1,2})[\s\-\.]*([A-Z]{3})[\s\-\.]*(\d{2,4})", date_str)
    if m:
        day = int(m.group(1))
        mon_str = m.group(2)
        year_str = m.group(3)
        if mon_str in month_names:
            month = month_names[mon_str]
            year = int(year_str)
            if year < 100:
                year = 1900 + year if year >= 50 else 2000 + year
            try:
                return datetime(year, month, day).strftime("%Y-%m-%d")
            except ValueError:
                pass

    # 4. Check 6-digit MRZ YYMMDD
    if len(date_str) == 6 and date_str.isdigit():
        return convert_mrz_date(date_str, as_iso=True)

    # Return cleaned string if all parsers fail
    return date_str


def convert_mrz_date(date_value, date_type=None, as_iso=True):
    """
    Convert MRZ YYMMDD format into ISO YYYY-MM-DD (or DD/MM/YYYY if as_iso=False).
    """
    if not date_value:
        return None

    try:
        date_value = str(date_value).strip()
        if len(date_value) != 6 or not date_value.isdigit():
            return None

        year = int(date_value[0:2])
        month = int(date_value[2:4])
        day = int(date_value[4:6])

        if month < 1 or month > 12 or day < 1 or day > 31:
            return None

        # MRZ century rule
        if year >= 50:
            full_year = 1900 + year
        else:
            full_year = 2000 + year

        dt = datetime(full_year, month, day)
        return dt.strftime("%Y-%m-%d") if as_iso else dt.strftime("%d/%m/%Y")
    except ValueError:
        return None


def normalize_gender(gender_val):
    """
    Normalizes gender representations to standard ISO single character 'M', 'F', 'X', or None.
    """
    if not gender_val:
        return None
    g = str(gender_val).strip().upper()
    if g in ["M", "MALE", "MAN", "MASCULINE", "HOMME", "VARÓN"]:
        return "M"
    if g in ["F", "FEMALE", "WOMAN", "FEMININE", "FEMME", "MUJER"]:
        return "F"
    if g in ["X", "OTHER", "NON-BINARY", "UNSPECIFIED", "<"]:
        return "X"
    return g if len(g) == 1 else None


def normalize_nationality(nationality):
    """
    Normalizes nationality to full descriptor or ISO 3-letter code.
    """
    if not nationality:
        return None

    nat_clean = nationality.upper().strip()

    country_to_nat = {
        "IND": "INDIAN",
        "INDIAN": "INDIAN",
        "INDIA": "INDIAN",
        "USA": "AMERICAN",
        "UNITED STATES": "AMERICAN",
        "AMERICAN": "AMERICAN",
        "GBR": "BRITISH",
        "UNITED KINGDOM": "BRITISH",
        "BRITISH": "BRITISH",
        "CAN": "CANADIAN",
        "CANADA": "CANADIAN",
        "CANADIAN": "CANADIAN",
        "AUS": "AUSTRALIAN",
        "AUSTRALIA": "AUSTRALIAN",
        "AUSTRALIAN": "AUSTRALIAN",
        "DEU": "GERMAN",
        "GERMANY": "GERMAN",
        "GERMAN": "GERMAN",
        "FRA": "FRENCH",
        "FRANCE": "FRENCH",
        "FRENCH": "FRENCH",
        "JPN": "JAPANESE",
        "JAPAN": "JAPANESE",
        "JAPANESE": "JAPANESE"
    }

    return country_to_nat.get(nat_clean, nat_clean)


def normalize_country_code(code_or_name):
    """
    Normalizes country code/name into standard ISO 3166-1 alpha-3 code.
    """
    if not code_or_name:
        return None
    c = str(code_or_name).upper().strip()
    mapping = {
        "INDIAN": "IND", "INDIA": "IND", "IND": "IND",
        "AMERICAN": "USA", "UNITED STATES": "USA", "USA": "USA", "US": "USA",
        "BRITISH": "GBR", "UNITED KINGDOM": "GBR", "GBR": "GBR", "UK": "GBR",
        "CANADIAN": "CAN", "CANADA": "CAN", "CAN": "CAN",
        "AUSTRALIAN": "AUS", "AUSTRALIA": "AUS", "AUS": "AUS",
        "GERMAN": "DEU", "GERMANY": "DEU", "DEU": "DEU",
        "FRENCH": "FRA", "FRANCE": "FRA", "FRA": "FRA",
        "JAPANESE": "JPN", "JAPAN": "JPN", "JPN": "JPN"
    }
    return mapping.get(c, c[:3] if len(c) >= 3 else c)