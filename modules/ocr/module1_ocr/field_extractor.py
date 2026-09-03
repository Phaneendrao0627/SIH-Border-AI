import re


def convert_month_date(date_text):

    months = {
        "JAN": "01",
        "FEB": "02",
        "MAR": "03",
        "APR": "04",
        "MAY": "05",
        "JUN": "06",
        "JUL": "07",
        "AUG": "08",
        "SEP": "09",
        "OCT": "10",
        "NOV": "11",
        "DEC": "12"
    }

    match = re.search(
        r"(\d{1,2})\s+([A-Z]{3})\s+(\d{2,4})",
        date_text.upper()
    )

    if not match:
        return None

    day = match.group(1).zfill(2)
    month = months.get(match.group(2))
    year = match.group(3)

    if not month:
        return None

    if len(year) == 2:

        year_int = int(year)

        if year_int >= 30:
            year = "19" + year
        else:
            year = "20" + year

    return f"{day}/{month}/{year}"


def extract_passport_fields(text):

    data = {
        "document_type": "Passport",
        "passport_number": None,
        "surname": None,
        "given_name": None,
        "nationality": None,
        "date_of_birth": None,
        "gender": None,
        "place_of_birth": None,
        "place_of_issue": None,
        "date_of_issue": None,
        "date_of_expiry": None
    }

    # --------------------------------------------------
    # NORMALIZE TEXT
    # --------------------------------------------------

    text = text.replace("\n", " ")

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    # --------------------------------------------------
    # PASSPORT NUMBER
    # --------------------------------------------------

    patterns = [

        # Norway style
        r"Passport number.*?\b([A-Z]{1,3}\d{6,9})\b",

        # General passport number
        r"\b([A-Z]\d{7,9})\b",

        # Numeric passport number
        r"\b(\d{8,9})\b"
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            data["passport_number"] = (
                match.group(1).upper()
            )

            break

    # --------------------------------------------------
    # SURNAME
    # --------------------------------------------------

    match = re.search(
        r"Surname.*?\b([A-ZÆØÅÖÄÜÉÑ\-]{3,})\b",
        text,
        re.IGNORECASE
    )

    if match:

        data["surname"] = match.group(1).upper()

    # --------------------------------------------------
    # GIVEN NAME
    # --------------------------------------------------

    match = re.search(
        r"(?:First and middle names|Given names).*?"
        r"\b([A-ZÆØÅÖÄÜÉÑ\-]{3,}(?:\s+[A-ZÆØÅÖÄÜÉÑ\-]{2,})*)\b",
        text,
        re.IGNORECASE
    )

    if match:

        data["given_name"] = match.group(1).upper()

    # --------------------------------------------------
    # NATIONALITY
    # --------------------------------------------------

    if re.search(
        r"NORSK|NORWEGIAN",
        text,
        re.IGNORECASE
    ):

        data["nationality"] = "NORWEGIAN"

    elif re.search(
        r"INDIAN|INOIAN|IND1AN|INDlAN",
        text,
        re.IGNORECASE
    ):

        data["nationality"] = "INDIAN"

    # --------------------------------------------------
    # GENDER
    # --------------------------------------------------

    match = re.search(
        r"\bSex\b.*?\b([MF])\b",
        text,
        re.IGNORECASE
    )

    if match:

        data["gender"] = match.group(1).upper()

    # --------------------------------------------------
    # DATE OF BIRTH
    # --------------------------------------------------

    match = re.search(
        r"(?:Date of birth).*?"
r"(\d{1,2}\s+[A-Z]{3}(?:\s*/?[A-Z]{3})?\s+\d{2,4})",
        text,
        re.IGNORECASE
    )

    if match:

        data["date_of_birth"] = convert_month_date(
            match.group(1)
        )

    else:

        match = re.search(
            r"\b(\d{2}/\d{2}/\d{4})\b",
            text
        )

        if match:

            data["date_of_birth"] = match.group(1)

    # --------------------------------------------------
    # DATE OF EXPIRY
    # --------------------------------------------------

    match = re.search(
        r"(?:Date of expiry).*?"
        r"(\d{1,2}\s+[A-Z]{3}\s+\d{2,4})",
        text,
        re.IGNORECASE
    )

    if match:

        data["date_of_expiry"] = convert_month_date(
            match.group(1)
        )

    # --------------------------------------------------
    # PLACE OF BIRTH
    # --------------------------------------------------

    match = re.search(
        r"(?:Place of birth).*?"
        r"\b([A-Z]{2,})\b",
        text,
        re.IGNORECASE
    )

    if match:

        data["place_of_birth"] = match.group(1).upper()

    # --------------------------------------------------
    # PLACE OF ISSUE
    # --------------------------------------------------

    if re.search(
        r"HYDERABAD",
        text,
        re.IGNORECASE
    ):

        data["place_of_issue"] = "HYDERABAD"

    # --------------------------------------------------
    # RETURN DATA
    # --------------------------------------------------

    return data