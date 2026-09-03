import json
import os
from datetime import datetime

OCR_FILE = "output/ocr_data.json"
MRZ_FILE = "output/mrz_data.json"
OUTPUT_FILE = "output/final_document.json"


def load_json(path):
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"File not found: {path}\n"
            f"Run the required extraction script first."
        )

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize(value):
    """Normalize text for comparison."""
    if value is None:
        return None

    return (
        str(value)
        .upper()
        .replace(" ", "")
        .replace("<", "")
        .strip()
    )


def compare_values(ocr_value, mrz_value):
    """Compare OCR and MRZ values safely."""
    if not ocr_value or not mrz_value:
        return None

    return normalize(ocr_value) == normalize(mrz_value)


def nationality_match(ocr_value, mrz_value):
    """
    Compare:
        INDIAN <-> IND
        NORWEGIAN <-> NOR
    """

    if not ocr_value or not mrz_value:
        return None

    mapping = {
        "INDIAN": "IND",
        "NORWEGIAN": "NOR",
        "AMERICAN": "USA",
        "BRITISH": "GBR",
        "CANADIAN": "CAN",
        "AUSTRALIAN": "AUS",
        "GERMAN": "DEU",
        "FRENCH": "FRA",
        "ITALIAN": "ITA",
        "SPANISH": "ESP",
        "JAPANESE": "JPN",
        "CHINESE": "CHN",
    }

    ocr = normalize(ocr_value)
    mrz = normalize(mrz_value)

    if ocr == mrz:
        return True

    return mapping.get(ocr) == mrz


def calculate_confidence(
    passport_match,
    surname_match,
    nationality_match_result,
    dob_match,
    gender_match,
    expiry_match,
    mrz_score,
):
    """
    Calculate confidence using only fields that actually exist.
    """

    checks = []

    for result in [
        passport_match,
        surname_match,
        nationality_match_result,
        dob_match,
        gender_match,
        expiry_match,
    ]:
        if result is not None:
            checks.append(result)

    if not checks:
        return 0

    successful = sum(checks)
    consistency_score = (successful / len(checks)) * 100

    # MRZ validity contributes to final confidence.
    final_score = round(
        (consistency_score * 0.6) +
        (float(mrz_score) * 0.4)
    )

    return min(final_score, 100)


# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------

ocr = load_json(OCR_FILE)
mrz = load_json(MRZ_FILE)


# ---------------------------------------------------------
# EXTRACT OCR VALUES
# ---------------------------------------------------------

ocr_document_type = ocr.get("document_type")

ocr_passport = ocr.get("passport_number")
ocr_surname = ocr.get("surname")
ocr_given_name = ocr.get("given_name")
ocr_nationality = ocr.get("nationality")
ocr_dob = ocr.get("date_of_birth")
ocr_gender = ocr.get("gender")
ocr_place_of_birth = ocr.get("place_of_birth")
ocr_place_of_issue = ocr.get("place_of_issue")
ocr_date_of_issue = ocr.get("date_of_issue")
ocr_expiry = ocr.get("date_of_expiry")


# ---------------------------------------------------------
# EXTRACT MRZ VALUES
# ---------------------------------------------------------

mrz_document_type = mrz.get("document_type")

mrz_passport = mrz.get("passport_number")

if mrz_passport:
    mrz_passport = mrz_passport.replace("<", "").strip()
mrz_surname = mrz.get("surname")
mrz_given_name = mrz.get("given_name")
mrz_nationality = mrz.get("nationality")
mrz_dob = mrz.get("date_of_birth_formatted")
mrz_gender = mrz.get("gender")
mrz_expiry = mrz.get("date_of_expiry_formatted")

mrz_type = mrz.get("mrz_type")
mrz_score = mrz.get("mrz_valid_score", 0)

valid_passport = mrz.get("valid_passport_number")
valid_dob = mrz.get("valid_date_of_birth")
valid_expiry = mrz.get("valid_date_of_expiry")


# ---------------------------------------------------------
# CONSISTENCY CHECKS
# ---------------------------------------------------------

passport_match = compare_values(
    ocr_passport,
    mrz_passport
)

surname_match = compare_values(
    ocr_surname,
    mrz_surname
)

given_name_match = compare_values(
    ocr_given_name,
    mrz_given_name
)

nationality_match_result = nationality_match(
    ocr_nationality,
    mrz_nationality
)

dob_match = compare_values(
    ocr_dob,
    mrz_dob
)

gender_match = compare_values(
    ocr_gender,
    mrz_gender
)

expiry_match = compare_values(
    ocr_expiry,
    mrz_expiry
)


# ---------------------------------------------------------
# CONFIDENCE
# ---------------------------------------------------------

confidence_score = calculate_confidence(
    passport_match,
    surname_match,
    nationality_match_result,
    dob_match,
    gender_match,
    expiry_match,
    mrz_score
)


if confidence_score >= 85:
    confidence_level = "HIGH"
elif confidence_score >= 65:
    confidence_level = "MEDIUM"
else:
    confidence_level = "LOW"


# ---------------------------------------------------------
# FINAL DOCUMENT
# ---------------------------------------------------------

final_data = {
    "document_type": mrz_document_type or ocr_document_type,

    "identity": {
        "surname": mrz_surname or ocr_surname,
        "given_name": mrz_given_name or ocr_given_name,
        "nationality": (
            ocr_nationality
            if ocr_nationality
            else mrz_nationality
        ),
        "gender": mrz_gender or ocr_gender
    },

    "passport": {
        "passport_number": {
            "value": mrz_passport or ocr_passport,
            "source": "MRZ" if mrz_passport else "OCR",
            "mrz_verified": bool(valid_passport),
            "ocr_value": ocr_passport,
            "sources_match": passport_match
        },

        "date_of_birth": mrz_dob or ocr_dob,

        "date_of_expiry": mrz_expiry or ocr_expiry
    },

    "place_information": {
        "place_of_birth": (
            ocr_place_of_birth
            if ocr_place_of_birth
            else None
        ),

        "place_of_issue": (
            ocr_place_of_issue
            if ocr_place_of_issue
            else None
        )
    },

    "date_information": {
        "date_of_issue": ocr_date_of_issue
    },

    "mrz_verification": {
        "mrz_type": mrz_type,
        "valid_score": mrz_score,
        "valid_passport_number": valid_passport,
        "valid_date_of_birth": valid_dob,
        "valid_date_of_expiry": valid_expiry
    },

    "consistency_check": {
        "passport_number_match": passport_match,
        "surname_match": surname_match,
        "given_name_match": given_name_match,
        "nationality_match": nationality_match_result,
        "gender_match": gender_match,
        "date_of_birth_match": dob_match,
        "date_of_expiry_match": expiry_match
    },

    "confidence": {
        "score": confidence_score,
        "level": confidence_level
    }
}


# ---------------------------------------------------------
# SAVE
# ---------------------------------------------------------

os.makedirs("output", exist_ok=True)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(final_data, f, indent=4, ensure_ascii=False)


# ---------------------------------------------------------
# DISPLAY
# ---------------------------------------------------------

print("\n========== FINAL DOCUMENT DATA ==========\n")
print(json.dumps(final_data, indent=4, ensure_ascii=False))
print("\n=========================================")
print("✅ Final document JSON created successfully!")
print(f"Saved to: {OUTPUT_FILE}")