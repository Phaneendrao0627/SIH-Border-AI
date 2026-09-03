def normalize_nationality(value):

    if not value:
        return None

    value = value.upper().strip()

    nationality_map = {
        "INDIAN": "IND",
        "IND": "IND",

        "NORWEGIAN": "NOR",
        "NOR": "NOR",

        "AMERICAN": "USA",
        "USA": "USA",

        "BRITISH": "GBR",
        "GBR": "GBR",

        "CANADIAN": "CAN",
        "CAN": "CAN",

        "AUSTRALIAN": "AUS",
        "AUS": "AUS"
    }

    return nationality_map.get(value, value)


def check_consistency(ocr_data, mrz_data):

    # ---------------------------------------------
    # PASSPORT NUMBER
    # ---------------------------------------------

    ocr_passport = ocr_data.get(
        "passport_number"
    )

    mrz_passport = mrz_data.get(
        "passport_number"
    )

    if ocr_passport and mrz_passport:

        passport_match = (
            ocr_passport.upper().strip()
            == mrz_passport.upper().strip()
        )

    else:

        passport_match = None

    # ---------------------------------------------
    # NATIONALITY
    # ---------------------------------------------

    ocr_nationality = normalize_nationality(
        ocr_data.get("nationality")
    )

    mrz_nationality = normalize_nationality(
        mrz_data.get("nationality")
    )

    if ocr_nationality and mrz_nationality:

        nationality_match = (
            ocr_nationality
            == mrz_nationality
        )

    else:

        nationality_match = None

    # ---------------------------------------------
    # GENDER
    # ---------------------------------------------

    ocr_gender = ocr_data.get("gender")
    mrz_gender = mrz_data.get("gender")

    if ocr_gender and mrz_gender:

        gender_match = (
            ocr_gender.upper()
            == mrz_gender.upper()
        )

    else:

        gender_match = None

    # ---------------------------------------------
    # RETURN
    # ---------------------------------------------

    return {
        "passport_number_match": passport_match,
        "nationality_match": nationality_match,
        "gender_match": gender_match
    }