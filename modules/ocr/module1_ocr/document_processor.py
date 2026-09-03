import json
import os
from datetime import datetime


# ============================================================
# CONFIGURATION
# ============================================================

OUTPUT_FOLDER = "output"

OCR_FILE = os.path.join(
    OUTPUT_FOLDER,
    "ocr_data.json"
)

MRZ_FILE = os.path.join(
    OUTPUT_FOLDER,
    "mrz_data.json"
)

FINAL_FILE = os.path.join(
    OUTPUT_FOLDER,
    "final_document.json"
)


# ============================================================
# DISPLAY FUNCTIONS
# ============================================================

def print_line():

    print(
        "=" * 70
    )


def print_section(title):

    print("\n")

    print_line()

    print(
        title.center(70)
    )

    print_line()


# ============================================================
# LOAD JSON FILE
# ============================================================

def load_json(file_path):

    if not os.path.exists(file_path):

        return None


    try:

        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(
                file
            )

        return data


    except Exception as error:

        print(
            f"⚠️ Error loading {file_path}"
        )

        print(
            error
        )

        return None


# ============================================================
# SAFE VALUE
# ============================================================

def safe_value(value):

    if value is None:

        return None


    if isinstance(
        value,
        str
    ):

        value = value.strip()

        if not value:

            return None


    return value


# ============================================================
# NORMALIZE TEXT
# ============================================================

def normalize_text(value):

    if not value:

        return None


    value = str(value)

    value = value.upper()

    value = value.strip()

    value = " ".join(
        value.split()
    )

    return value


# ============================================================
# NORMALIZE DATE
# ============================================================

def normalize_date(value):

    if not value:

        return None


    value = str(value).strip()


    # Already ISO format

    try:

        parsed_date = datetime.strptime(
            value,
            "%Y-%m-%d"
        )

        return parsed_date.strftime(
            "%Y-%m-%d"
        )

    except:

        pass


    # DD/MM/YYYY

    try:

        parsed_date = datetime.strptime(
            value,
            "%d/%m/%Y"
        )

        return parsed_date.strftime(
            "%Y-%m-%d"
        )

    except:

        pass


    # DD-MM-YYYY

    try:

        parsed_date = datetime.strptime(
            value,
            "%d-%m-%Y"
        )

        return parsed_date.strftime(
            "%Y-%m-%d"
        )

    except:

        pass


    # DD.MM.YYYY

    try:

        parsed_date = datetime.strptime(
            value,
            "%d.%m.%Y"
        )

        return parsed_date.strftime(
            "%Y-%m-%d"
        )

    except:

        pass


    return value


# ============================================================
# COMPARE VALUES
# ============================================================

def compare_values(
    ocr_value,
    mrz_value,
    is_date=False
):

    ocr_value = safe_value(
        ocr_value
    )

    mrz_value = safe_value(
        mrz_value
    )


    # --------------------------------------------------------
    # BOTH MISSING
    # --------------------------------------------------------

    if (
        not ocr_value
        and not mrz_value
    ):

        return "BOTH_MISSING"


    # --------------------------------------------------------
    # OCR MISSING
    # --------------------------------------------------------

    if not ocr_value:

        return "MISSING_OCR"


    # --------------------------------------------------------
    # MRZ MISSING
    # --------------------------------------------------------

    if not mrz_value:

        return "MISSING_MRZ"


    # --------------------------------------------------------
    # DATE COMPARISON
    # --------------------------------------------------------

    if is_date:

        normalized_ocr = normalize_date(
            ocr_value
        )

        normalized_mrz = normalize_date(
            mrz_value
        )


        if (
            normalized_ocr
            ==
            normalized_mrz
        ):

            return "MATCH"


        return "DIFFERENT"


    # --------------------------------------------------------
    # NORMAL TEXT COMPARISON
    # --------------------------------------------------------

    normalized_ocr = normalize_text(
        ocr_value
    )

    normalized_mrz = normalize_text(
        mrz_value
    )


    if (
        normalized_ocr
        ==
        normalized_mrz
    ):

        return "MATCH"


    return "DIFFERENT"


# ============================================================
# CALCULATE OCR COMPLETENESS
# ============================================================

def calculate_ocr_completeness(
    ocr_data,
    document_type
):

    # --------------------------------------------------------
    # PASSPORT FIELDS
    # --------------------------------------------------------

    if document_type == "PASSPORT":

        fields = [

            "passport_number",
            "surname",
            "given_name",
            "nationality",
            "date_of_birth",
            "gender",
            "date_of_expiry"

        ]


    # --------------------------------------------------------
    # VISA FIELDS
    # --------------------------------------------------------

    elif document_type == "VISA":

        fields = [

            "passport_number",
            "surname",
            "given_name",
            "visa_number",
            "visa_type",
            "date_of_expiry"

        ]


    # --------------------------------------------------------
    # NATIONAL ID FIELDS
    # --------------------------------------------------------

    elif document_type == "NATIONAL ID":

        fields = [

            "id_number",
            "full_name",
            "date_of_birth",
            "gender"

        ]


    # --------------------------------------------------------
    # DRIVING LICENCE FIELDS
    # --------------------------------------------------------

    elif document_type == "DRIVING LICENCE":

        fields = [

            "license_number",
            "full_name",
            "date_of_birth"

        ]


    # --------------------------------------------------------
    # PERMIT FIELDS
    # --------------------------------------------------------

    elif document_type == "PERMIT":

        fields = [

            "permit_number"

        ]


    else:

        fields = []


    if not fields:

        return 0.0


    completed_fields = 0


    for field in fields:

        value = ocr_data.get(
            field
        )


        if safe_value(value):

            completed_fields += 1


    score = (
        completed_fields
        /
        len(fields)
    ) * 100


    return round(
        score,
        2
    )


# ============================================================
# CALCULATE CONSISTENCY SCORE
# ============================================================

def calculate_consistency_score(
    comparisons
):

    valid_comparisons = []


    for field, result in comparisons.items():

        if result == "MATCH":

            valid_comparisons.append(
                1
            )


        elif result == "DIFFERENT":

            valid_comparisons.append(
                0
            )


    if not valid_comparisons:

        return 0


    score = (

        sum(
            valid_comparisons
        )

        /

        len(
            valid_comparisons
        )

    ) * 100


    return round(
        score,
        2
    )


# ============================================================
# CONFIDENCE LEVEL
# ============================================================

def get_confidence_level(score):

    if score >= 90:

        return "VERY HIGH"


    elif score >= 75:

        return "HIGH"


    elif score >= 50:

        return "MEDIUM"


    else:

        return "LOW"


# ============================================================
# CLEAN MRZ GIVEN NAME
# ============================================================

def clean_mrz_given_name(value):

    if not value:

        return None


    value = normalize_text(
        value
    )


    if not value:

        return None


    words = value.split()


    clean_words = []


    for word in words:

        # Remove obvious OCR garbage

        if len(word) > 12:

            continue


        if word.count("K") > 5:

            continue


        clean_words.append(
            word
        )


    if clean_words:

        return " ".join(
            clean_words
        )


    return value


# ============================================================
# GET OCR EXTRACTED DATA
# ============================================================

def get_extracted_ocr_data(
    ocr_data
):

    if not ocr_data:

        return {}


    # --------------------------------------------------------
    # NEW OCR ENGINE STRUCTURE
    # --------------------------------------------------------

    if (
        "extracted_data"
        in ocr_data
    ):

        extracted = ocr_data.get(
            "extracted_data",
            {}
        )


        if isinstance(
            extracted,
            dict
        ):

            return extracted


    # --------------------------------------------------------
    # OLD OCR STRUCTURE
    # --------------------------------------------------------

    return ocr_data


# ============================================================
# GET MRZ FIELD
# ============================================================

def get_mrz_field(
    mrz_data,
    field
):

    if not mrz_data:

        return None


    return mrz_data.get(
        field
    )


# ============================================================
# BUILD FULL NAME
# ============================================================

def build_full_name(
    surname,
    given_name
):

    name_parts = []


    if given_name:

        name_parts.append(
            str(given_name).strip()
        )


    if surname:

        name_parts.append(
            str(surname).strip()
        )


    if not name_parts:

        return None


    return " ".join(
        name_parts
    )


# ============================================================
# MAIN PROGRAM
# ============================================================

def main():


    # ========================================================
    # HEADER
    # ========================================================

    print_section(
        "DOCUMENT PROCESSOR"
    )


    # ========================================================
    # LOAD OCR DATA
    # ========================================================

    ocr_data = load_json(
        OCR_FILE
    )


    if not ocr_data:

        print(
            "❌ OCR data not found."
        )

        print(
            f"Expected file: {OCR_FILE}"
        )

        return


    print(
        "\nOCR data loaded: ✅"
    )


    # ========================================================
    # GET EXTRACTED OCR DATA
    # ========================================================

    extracted_ocr_data = get_extracted_ocr_data(
        ocr_data
    )


    print(
        "OCR extracted fields loaded: ✅"
    )


    # ========================================================
    # LOAD MRZ DATA
    # ========================================================

    mrz_data = load_json(
        MRZ_FILE
    )


    if mrz_data:

        print(
            "MRZ data loaded: ✅"
        )

    else:

        print(
            "MRZ data loaded: ❌"
        )


    # ========================================================
    # DOCUMENT TYPE
    # ========================================================

    document_type = ocr_data.get(
        "document_type"
    )


    if not document_type:

        document_type = extracted_ocr_data.get(
            "document_type"
        )


    if not document_type:

        document_type = "UNKNOWN"


    document_type = document_type.upper()


    print(
        f"\nDocument type: {document_type}"
    )


    # ========================================================
    # PROCESS PASSPORT
    # ========================================================

    if document_type == "PASSPORT":

        print(
            "\nProcessing Passport..."
        )


        # ----------------------------------------------------
        # OCR FIELDS
        # ----------------------------------------------------

        ocr_passport_number = extracted_ocr_data.get(
            "passport_number"
        )

        ocr_surname = extracted_ocr_data.get(
            "surname"
        )

        ocr_given_name = extracted_ocr_data.get(
            "given_name"
        )

        ocr_nationality = extracted_ocr_data.get(
            "nationality"
        )

        ocr_date_of_birth = extracted_ocr_data.get(
            "date_of_birth"
        )

        ocr_gender = extracted_ocr_data.get(
            "gender"
        )

        ocr_date_of_issue = extracted_ocr_data.get(
            "date_of_issue"
        )

        ocr_date_of_expiry = extracted_ocr_data.get(
            "date_of_expiry"
        )

        ocr_place_of_birth = extracted_ocr_data.get(
            "place_of_birth"
        )

        ocr_place_of_issue = extracted_ocr_data.get(
            "place_of_issue"
        )


        # ----------------------------------------------------
        # MRZ FIELDS
        # ----------------------------------------------------

        mrz_available = False

        mrz_valid = False

        mrz_confidence = 0.0


        if mrz_data:

            mrz_available = True


            validation = mrz_data.get(
                "validation",
                {}
            )


            mrz_valid = validation.get(
                "mrz_valid",
                False
            )


            mrz_confidence = mrz_data.get(
                "mrz_confidence",
                0.0
            )


        mrz_passport_number = get_mrz_field(
            mrz_data,
            "passport_number"
        )

        mrz_surname = get_mrz_field(
            mrz_data,
            "surname"
        )

        mrz_given_name = clean_mrz_given_name(

            get_mrz_field(
                mrz_data,
                "given_name"
            )

        )

        mrz_nationality = get_mrz_field(
            mrz_data,
            "nationality"
        )

        mrz_date_of_birth = get_mrz_field(
            mrz_data,
            "date_of_birth"
        )

        mrz_gender = get_mrz_field(
            mrz_data,
            "sex"
        )

        mrz_date_of_expiry = get_mrz_field(
            mrz_data,
            "date_of_expiry"
        )


        # ----------------------------------------------------
        # PREFER VALID MRZ DATA
        # ----------------------------------------------------

        if mrz_valid:

            final_passport_number = (

                mrz_passport_number
                or
                ocr_passport_number

            )

            final_surname = (

                mrz_surname
                or
                ocr_surname

            )

            final_given_name = (

                mrz_given_name
                or
                ocr_given_name

            )

            final_nationality = (

                mrz_nationality
                or
                ocr_nationality

            )

            final_date_of_birth = (

                mrz_date_of_birth
                or
                normalize_date(
                    ocr_date_of_birth
                )

            )

            final_gender = (

                mrz_gender
                or
                ocr_gender

            )

            final_date_of_expiry = (

                mrz_date_of_expiry
                or
                normalize_date(
                    ocr_date_of_expiry
                )

            )


        else:

            final_passport_number = (
                ocr_passport_number
            )

            final_surname = (
                ocr_surname
            )

            final_given_name = (
                ocr_given_name
            )

            final_nationality = (
                ocr_nationality
            )

            final_date_of_birth = (
                normalize_date(
                    ocr_date_of_birth
                )
            )

            final_gender = (
                ocr_gender
            )

            final_date_of_expiry = (
                normalize_date(
                    ocr_date_of_expiry
                )
            )


        # ----------------------------------------------------
        # FIELD COMPARISONS
        # ----------------------------------------------------

        comparisons = {

            "passport_number":

                compare_values(

                    ocr_passport_number,

                    mrz_passport_number

                ),


            "surname":

                compare_values(

                    ocr_surname,

                    mrz_surname

                ),


            "given_name":

                compare_values(

                    ocr_given_name,

                    mrz_given_name

                ),


            "nationality":

                compare_values(

                    ocr_nationality,

                    mrz_nationality

                ),


            "date_of_birth":

                compare_values(

                    ocr_date_of_birth,

                    mrz_date_of_birth,

                    True

                ),


            "gender":

                compare_values(

                    ocr_gender,

                    mrz_gender

                ),


            "date_of_expiry":

                compare_values(

                    ocr_date_of_expiry,

                    mrz_date_of_expiry,

                    True

                )

        }


        # ----------------------------------------------------
        # SCORES
        # ----------------------------------------------------

        ocr_completeness_score = (

            calculate_ocr_completeness(

                extracted_ocr_data,

                document_type

            )

        )


        consistency_score = (

            calculate_consistency_score(

                comparisons

            )

        )


        # ----------------------------------------------------
        # MRZ VALIDATION SCORE
        # ----------------------------------------------------

        if mrz_valid:

            mrz_validation_score = 100.0

        else:

            mrz_validation_score = float(
                mrz_confidence
            )


        # ----------------------------------------------------
        # CONFIDENCE SCORE
        # ----------------------------------------------------

        if mrz_valid:

            confidence_score = (

                mrz_validation_score * 0.50

                +

                consistency_score * 0.30

                +

                ocr_completeness_score * 0.20

            )

        else:

            confidence_score = (

                ocr_completeness_score * 0.70

                +

                consistency_score * 0.30

            )


        confidence_score = round(

            confidence_score,2

        )


        confidence_level = (

            get_confidence_level(

                confidence_score

            )

        )


        # ----------------------------------------------------
        # DOCUMENT STATUS
        # ----------------------------------------------------

        if mrz_valid:

            status = "VERIFIED"

        elif confidence_score >= 70:

            status = "PROCESSED"

        else:

            status = "REVIEW_REQUIRED"


        # ----------------------------------------------------
        # BUILD FULL NAME
        # ----------------------------------------------------

        full_name = build_full_name(

            final_surname,

            final_given_name

        )


        # ----------------------------------------------------
        # FINAL DOCUMENT
        # ----------------------------------------------------

        final_document = {

            "document_type":

                document_type,


            "status":

                status,


            "identity": {

                "full_name":

                    full_name,


                "surname":

                    final_surname,


                "given_name":

                    final_given_name,


                "nationality":

                    final_nationality,


                "date_of_birth":

                    final_date_of_birth,


                "gender":

                    final_gender

            },


            "document": {

                "document_number":

                    final_passport_number,


                "date_of_issue":

                    normalize_date(
                        ocr_date_of_issue
                    ),


                "date_of_expiry":

                    final_date_of_expiry,


                "place_of_birth":

                    ocr_place_of_birth,


                "place_of_issue":

                    ocr_place_of_issue

            },


            "additional_information": {

                "visa_number":

                    None,


                "visa_type":

                    None,


                "number_of_entries":

                    None,


                "endorsement":

                    None,


                "id_number":

                    None,


                "license_number":

                    None,


                "permit_number":

                    None

            },


            "verification": {

                "mrz_available":

                    mrz_available,


                "mrz_valid":

                    mrz_valid,


                "mrz_validation_score":

                    mrz_validation_score,


                "ocr_completeness_score":

                    ocr_completeness_score,


                "consistency_score":

                    consistency_score,


                "confidence_score":

                    confidence_score,


                "confidence_level":

                    confidence_level,


                "field_comparisons":

                    comparisons

            }

        }


    # ========================================================
    # PROCESS NON-PASSPORT DOCUMENT
    # ========================================================

    else:

        print(
            "\nProcessing non-passport document..."
        )


        ocr_completeness_score = (

            calculate_ocr_completeness(

                extracted_ocr_data,

                document_type

            )

        )


        confidence_score = (

            ocr_completeness_score

        )


        confidence_level = (

            get_confidence_level(

                confidence_score

            )

        )


        if confidence_score >= 70:

            status = "PROCESSED"

        else:

            status = "REVIEW_REQUIRED"


        full_name = (

            extracted_ocr_data.get(
                "full_name"
            )

        )


        final_document = {

            "document_type":

                document_type,


            "status":

                status,


            "identity": {

                "full_name":

                    full_name,


                "surname":

                    extracted_ocr_data.get(
                        "surname"
                    ),


                "given_name":

                    extracted_ocr_data.get(
                        "given_name"
                    ),


                "nationality":

                    extracted_ocr_data.get(
                        "nationality"
                    ),


                "date_of_birth":

                    normalize_date(

                        extracted_ocr_data.get(
                            "date_of_birth"
                        )

                    ),


                "gender":

                    extracted_ocr_data.get(
                        "gender"
                    )

            },


            "document": {

                "document_number":

                    extracted_ocr_data.get(
                        "passport_number"
                    )

                    or

                    extracted_ocr_data.get(
                        "visa_number"
                    )

                    or

                    extracted_ocr_data.get(
                        "id_number"
                    )

                    or

                    extracted_ocr_data.get(
                        "license_number"
                    )

                    or

                    extracted_ocr_data.get(
                        "permit_number"
                    ),


                "date_of_issue":

                    normalize_date(

                        extracted_ocr_data.get(
                            "date_of_issue"
                        )

                    ),


                "date_of_expiry":

                    normalize_date(

                        extracted_ocr_data.get(
                            "date_of_expiry"
                        )

                    ),


                "place_of_birth":

                    extracted_ocr_data.get(
                        "place_of_birth"
                    ),


                "place_of_issue":

                    extracted_ocr_data.get(
                        "place_of_issue"
                    )

            },


            "additional_information": {

                "visa_number":

                    extracted_ocr_data.get(
                        "visa_number"
                    ),


                "visa_type":

                    extracted_ocr_data.get(
                        "visa_type"
                    ),


                "number_of_entries":

                    extracted_ocr_data.get(
                        "number_of_entries"
                    ),


                "endorsement":

                    extracted_ocr_data.get(
                        "endorsement"
                    ),


                "id_number":

                    extracted_ocr_data.get(
                        "id_number"
                    ),


                "license_number":

                    extracted_ocr_data.get(
                        "license_number"
                    ),


                "permit_number":

                    extracted_ocr_data.get(
                        "permit_number"
                    )

            },


            "verification": {

                "mrz_available":

                    False,


                "mrz_valid":

                    False,


                "mrz_validation_score":

                    0.0,


                "ocr_completeness_score":

                    ocr_completeness_score,


                "consistency_score":

                    0.0,


                "confidence_score":

                    confidence_score,


                "confidence_level":

                    confidence_level,


                "field_comparisons":

                    {}

            }

        }


    # ========================================================
    # DISPLAY OUTPUT
    # ========================================================

    print_section(
        "STANDARDIZED OUTPUT"
    )


    print(
        json.dumps(

            final_document,

            indent=4,

            ensure_ascii=False

        )

    )


    # ========================================================
    # VERIFICATION SUMMARY
    # ========================================================

    print_section(
        "VERIFICATION SUMMARY"
    )


    verification = final_document.get(
        "verification",
        {}
    )


    comparisons = verification.get(
        "field_comparisons",
        {}
    )


    if comparisons:

        for field, result in comparisons.items():

            field_name = (

                field.replace(
                    "_",
                    " "
                ).title()

            )


            if result == "MATCH":

                symbol = "✅"


            elif result == "DIFFERENT":

                symbol = "⚠️"


            elif result == "MISSING_OCR":

                symbol = "❓"


            elif result == "MISSING_MRZ":

                symbol = "❓"


            else:

                symbol = "➖"


            print(

                f"{field_name:<25} "

                f"{symbol} {result}"

            )


    print()

    print(
        "-" * 70
    )


    print(

        f"MRZ Available        : "

        f"{verification.get('mrz_available')}"

    )


    print(

        f"MRZ Valid            : "

        f"{verification.get('mrz_valid')}"

    )


    print(

        f"MRZ Validation Score : "

        f"{verification.get('mrz_validation_score')}%"

    )


    print(

        f"OCR Completeness     : "

        f"{verification.get('ocr_completeness_score')}%"

    )


    print(

        f"Consistency Score    : "

        f"{verification.get('consistency_score')}%"

    )


    print(

        f"Confidence Score     : "

        f"{verification.get('confidence_score')}%"

    )


    print(

        f"Confidence Level     : "

        f"{verification.get('confidence_level')}"

    )


    print(

        f"Document Status      : "

        f"{final_document.get('status')}"

    )


    # ========================================================
    # SAVE FINAL DOCUMENT
    # ========================================================

    os.makedirs(

        OUTPUT_FOLDER,

        exist_ok=True

    )


    with open(

        FINAL_FILE,

        "w",

        encoding="utf-8"

    ) as file:

        json.dump(

            final_document,

            file,

            indent=4,

            ensure_ascii=False

        )


    # ========================================================
    # COMPLETION
    # ========================================================

    print_section(
        "DOCUMENT PROCESSING COMPLETE"
    )


    print(

        "\nFinal document saved to:"

    )


    print(

        FINAL_FILE

    )


# ============================================================
# RUN PROGRAM
# ============================================================

if __name__ == "__main__":

    main()