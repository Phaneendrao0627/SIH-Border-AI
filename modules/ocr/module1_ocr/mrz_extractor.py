import json
import os
import sys

import pytesseract

# ============================================================
# TESSERACT CONFIGURATION
# ============================================================

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

from passporteye import read_mrz


# ============================================================
# CONFIGURATION
# ============================================================

IMAGE_PATH = os.path.join("input", "passport.jpg")
OUTPUT_PATH = os.path.join("output", "mrz_data.json")

print(f"Using image: {IMAGE_PATH}")


# ============================================================
# CHECK IMAGE
# ============================================================

if not os.path.isfile(IMAGE_PATH):
    print(f"❌ Passport image not found:")
    print(f"   {IMAGE_PATH}")
    sys.exit(1)


# ============================================================
# READ MRZ
# ============================================================

print("\nReading passport MRZ...\n")

try:
    mrz = read_mrz(IMAGE_PATH)

except Exception as e:
    print("❌ MRZ extraction failed.")
    print(f"Error: {e}")
    sys.exit(1)


# ============================================================
# CHECK MRZ
# ============================================================

if mrz is None:
    print("❌ MRZ could not be detected.")
    sys.exit(1)


# Convert PassportEye object to dictionary
data = mrz.to_dict()


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def clean_text(value):
    """Clean MRZ text fields."""

    if value is None:
        return None

    value = str(value).strip()

    # Remove MRZ filler characters at the end
    value = value.rstrip("<")

    # Convert multiple spaces to one
    value = " ".join(value.split())

    return value if value else None


def format_mrz_date(date):
    """
    Convert YYMMDD into DD/MM/YYYY.

    MRZ convention:
    50-99 -> 1950-1999
    00-49 -> 2000-2049
    """

    if not date:
        return None

    date = str(date).strip()

    if len(date) != 6 or not date.isdigit():
        return None

    year = int(date[0:2])
    month = date[2:4]
    day = date[4:6]

    if year >= 50:
        full_year = 1900 + year
    else:
        full_year = 2000 + year

    return f"{day}/{month}/{full_year}"


# ============================================================
# EXTRACT RAW MRZ VALUES
# ============================================================

passport_number = clean_text(
    data.get("number")
)

surname = clean_text(
    data.get("surname")
)

given_name = clean_text(
    data.get("names")
)

nationality = clean_text(
    data.get("nationality")
)

date_of_birth = clean_text(
    data.get("date_of_birth")
)

gender = clean_text(
    data.get("sex")
)

date_of_expiry = clean_text(
    data.get("expiration_date")
)


# ============================================================
# NORMALIZE NATIONALITY
# ============================================================

if nationality == "IND":
    nationality_display = "INDIAN"
else:
    nationality_display = nationality


# ============================================================
# NORMALIZE MRZ TYPE
# ============================================================

raw_mrz_type = data.get("type")

if raw_mrz_type in ["P", "P<", "TD3"]:
    mrz_type = "TD3"
elif raw_mrz_type in ["TD2"]:
    mrz_type = "TD2"
elif raw_mrz_type in ["TD1"]:
    mrz_type = "TD1"
else:
    mrz_type = raw_mrz_type


# ============================================================
# FORMAT DATES
# ============================================================

dob_formatted = format_mrz_date(
    date_of_birth
)

expiry_formatted = format_mrz_date(
    date_of_expiry
)


# ============================================================
# VALIDATION VALUES
# ============================================================

valid_score = data.get("valid_score")

valid_passport_number = data.get(
    "valid_number"
)

valid_date_of_birth = data.get(
    "valid_date_of_birth"
)

valid_date_of_expiry = data.get(
    "valid_expiration_date"
)


# ============================================================
# FINAL MRZ DATA
# ============================================================

mrz_data = {

    "document_type": "Passport",

    "mrz_type": mrz_type,

    "passport_number": passport_number,

    "surname": surname,

    "given_name": given_name,

    "nationality": nationality_display,

    "nationality_code": nationality,

    "date_of_birth": date_of_birth,

    "date_of_birth_formatted": dob_formatted,

    "gender": gender,

    "date_of_expiry": date_of_expiry,

    "date_of_expiry_formatted": expiry_formatted,

    "mrz_valid_score": valid_score,

    "valid_passport_number": valid_passport_number,

    "valid_date_of_birth": valid_date_of_birth,

    "valid_date_of_expiry": valid_date_of_expiry
}


# ============================================================
# DISPLAY
# ============================================================

print("========== CLEAN MRZ DATA ==========")

for key, value in mrz_data.items():
    print(f"{key}: {value}")

print("====================================")


# ============================================================
# SAVE JSON
# ============================================================

os.makedirs(
    "output",
    exist_ok=True
)

with open(
    OUTPUT_PATH,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        mrz_data,
        file,
        indent=4,
        ensure_ascii=False
    )


print("\n✅ MRZ JSON created successfully!")
print(f"Saved to: {OUTPUT_PATH}")