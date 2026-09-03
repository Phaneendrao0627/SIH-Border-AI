# ============================================================
# AI-BASED FAKE IDENTITY & DOCUMENT SCREENING SYSTEM
# MRZ ENGINE - PASSPORT TD3
# ============================================================

import json
import re
import os


# ============================================================
# FILE CONFIGURATION
# ============================================================

OCR_FILE = "output/ocr_data.json"
MRZ_FILE = "output/mrz_data.json"


# ============================================================
# HEADER
# ============================================================

print()
print("=" * 70)
print("                         MRZ ENGINE")
print("=" * 70)
print()


# ============================================================
# LOAD OCR JSON
# ============================================================

if not os.path.exists(OCR_FILE):

    print("❌ OCR data file not found:")
    print(OCR_FILE)
    exit()


with open(
    OCR_FILE,
    "r",
    encoding="utf-8"
) as file:

    ocr_data = json.load(file)


print("OCR data loaded: ✅")


# ============================================================
# DOCUMENT TYPE
# ============================================================

document_type = ocr_data.get(
    "document_type",
    "Unknown"
)

print(
    "Document type:",
    document_type
)

print()


if document_type != "Passport":

    print("⚠️ MRZ processing is currently enabled for passports only.")
    exit()


# ============================================================
# RAW OCR TEXT
# ============================================================

raw_text = ocr_data.get(
    "raw_text",
    ""
)

if not raw_text:

    print("❌ Raw OCR text is empty.")
    exit()


# ============================================================
# MRZ CHARACTER CLEANING
# ============================================================

def clean_line(line):

    line = line.upper()

    # Common OCR symbols that represent <
    line = line.replace("«", "<")
    line = line.replace("‹", "<")
    line = line.replace("›", "<")
    line = line.replace("|", "<")

    # Remove spaces
    line = line.replace(" ", "")

    # Keep only MRZ characters
    line = re.sub(
        r"[^A-Z0-9<]",
        "",
        line
    )

    return line


# ============================================================
# OCR TEXT LINES
# ============================================================

all_lines = raw_text.splitlines()

cleaned_lines = []


for line in all_lines:

    cleaned = clean_line(line)

    if cleaned:

        cleaned_lines.append(cleaned)


# ============================================================
# MRZ LINE 1 CANDIDATES
# ============================================================

line1_candidates = []


for line in cleaned_lines:

    if line.startswith("P<"):

        if len(line) >= 25:

            line1_candidates.append(line)


# ============================================================
# MRZ LINE 2 CANDIDATES
# ============================================================

line2_candidates = []


for line in cleaned_lines:

    if len(line) < 25:

        continue


    # A passport MRZ second line normally
    # contains many digits.

    digit_count = len(
        re.findall(
            r"\d",
            line
        )
    )


    if digit_count >= 5:

        # Do not accidentally select normal OCR text
        if not line.startswith("P<"):

            line2_candidates.append(line)


# ============================================================
# CHECK CANDIDATES
# ============================================================

print("=" * 70)
print("                    MRZ CANDIDATES")
print("=" * 70)
print()


print("Line 1 candidates:")

for candidate in line1_candidates:

    print(candidate)


print()

print("Line 2 candidates:")

for candidate in line2_candidates:

    print(candidate)


print()


# ============================================================
# MRZ CHECK DIGIT
# ============================================================

def calculate_check_digit(value):

    weights = [7, 3, 1]

    total = 0


    for i, char in enumerate(value):

        if char.isdigit():

            number = int(char)

        elif "A" <= char <= "Z":

            number = (
                ord(char)
                -
                ord("A")
                +
                10
            )

        elif char == "<":

            number = 0

        else:

            number = 0


        total += (
            number
            *
            weights[i % 3]
        )


    return total % 10


# ============================================================
# CHECK DIGIT VALIDATION
# ============================================================

def check_digit_valid(value, expected):

    if not expected.isdigit():

        return False


    calculated = calculate_check_digit(value)

    return calculated == int(expected)


# ============================================================
# NORMALIZE LINE 1
# ============================================================

def normalize_line1(line):

    line = clean_line(line)


    # Passport TD3 line 1 must be 44 characters.
    #
    # If OCR has extra characters at the end,
    # remove them.
    #
    # If shorter, fill with <.

    if len(line) > 44:

        line = line[:44]


    elif len(line) < 44:

        line = line.ljust(
            44,
            "<"
        )


    return line


# ============================================================
# NORMALIZE LINE 2
# ============================================================

def normalize_line2(line):

    line = clean_line(line)


    # --------------------------------------------------------
    # IMPORTANT OCR CORRECTION
    # --------------------------------------------------------
    #
    # Your OCR produced:
    #
    # P3938806<41IND8204066F2608282...
    #
    # Correct MRZ is:
    #
    # P3938806<4IND8204066F2608282...
    #
    # The extra "1" appears between the passport
    # check digit and nationality.
    #
    # Detect this situation and remove it.
    # --------------------------------------------------------

    if len(line) >= 14:

        # Expected structure:
        #
        # 0-8  passport number field
        # 9    check digit
        # 10-12 nationality

        first_part = line[:10]

        next_part = line[10:14]


        if (
            re.fullmatch(
                r"[A-Z0-9<]{9}\d",
                first_part
            )
            and
            len(next_part) == 4
        ):

            # If position 10 looks like an OCR-inserted
            # 1/I and positions 11-13 form a country code,
            # remove the extra character.

            possible_extra = line[10]

            possible_country = line[11:14]


            if (
                possible_extra in ["1", "I"]
                and
                re.fullmatch(
                    r"[A-Z]{3}",
                    possible_country
                )
            ):

                line = (
                    line[:10]
                    +
                    line[11:]
                )


    # --------------------------------------------------------
    # OTHER COMMON CASE
    # --------------------------------------------------------

    # Example:
    # P3938806<4IND...
    #
    # If OCR reads I as 1 inside nationality,
    # convert it back to I.

    if len(line) >= 13:

        nationality_part = line[10:13]

        nationality_part = nationality_part.replace(
            "1",
            "I"
        )

        line = (
            line[:10]
            +
            nationality_part
            +
            line[13:]
        )


    # --------------------------------------------------------
    # FINAL LENGTH
    # --------------------------------------------------------

    if len(line) > 44:

        line = line[:44]


    elif len(line) < 44:

        line = line.ljust(
            44,
            "<"
        )


    return line


# ============================================================
# SCORE LINE 1
# ============================================================

def score_line1(line):

    score = 0


    if line.startswith("P<"):

        score += 20


    if len(line) == 44:

        score += 10


    if line[2:5] == "IND":

        score += 20


    # Correct separator between surname and given name
    if "<<" in line[5:]:

        score += 20


    # Names should contain letters
    if re.search(
        r"[A-Z]{3,}",
        line[5:]
    ):

        score += 10


    return score


# ============================================================
# SCORE LINE 2
# ============================================================

def score_line2(line):

    score = 0


    # Clean and correct first
    corrected = normalize_line2(line)


    if len(corrected) == 44:

        score += 10


    # Passport field
    passport_field = corrected[0:9]

    passport_check = corrected[9]


    if re.fullmatch(
        r"[A-Z0-9<]{9}",
        passport_field
    ):

        score += 10


    if passport_check.isdigit():

        score += 10


    # Nationality
    nationality = corrected[10:13]


    if re.fullmatch(
        r"[A-Z]{3}",
        nationality
    ):

        score += 15


    # DOB
    dob = corrected[13:19]

    if re.fullmatch(
        r"\d{6}",
        dob
    ):

        score += 15


    # Sex
    if corrected[20] in [
        "M",
        "F",
        "X",
        "<"
    ]:

        score += 10


    # Expiry
    expiry = corrected[21:27]

    if re.fullmatch(
        r"\d{6}",
        expiry
    ):

        score += 15


    # Check digits
    if (
        passport_check.isdigit()
        and
        check_digit_valid(
            passport_field,
            passport_check
        )
    ):

        score += 30


    if (
        corrected[19].isdigit()
        and
        check_digit_valid(
            dob,
            corrected[19]
        )
    ):

        score += 30


    if (
        corrected[27].isdigit()
        and
        check_digit_valid(
            expiry,
            corrected[27]
        )
    ):

        score += 30


    # Overall check
    overall_data = (
        corrected[0:10]
        +
        corrected[13:20]
        +
        corrected[21:28]
        +
        corrected[28:43]
    )


    if (
        corrected[43].isdigit()
        and
        check_digit_valid(
            overall_data,
            corrected[43]
        )
    ):

        score += 40


    return score


# ============================================================
# SELECT BEST LINE 1
# ============================================================

if not line1_candidates:

    print("❌ No passport MRZ line 1 found.")
    exit()


best_line1 = max(
    line1_candidates,
    key=score_line1
)


best_line1 = normalize_line1(
    best_line1
)


# ============================================================
# SELECT BEST LINE 2
# ============================================================

if not line2_candidates:

    print("❌ No passport MRZ line 2 found.")
    exit()


best_line2 = max(
    line2_candidates,
    key=score_line2
)


best_line2 = normalize_line2(
    best_line2
)


# ============================================================
# DISPLAY SELECTED MRZ
# ============================================================

print("=" * 70)
print("                    SELECTED MRZ")
print("=" * 70)
print()


print("MRZ Line 1:")
print(best_line1)

print()

print("MRZ Line 2:")
print(best_line2)

print()

print("Line 1 length:", len(best_line1))
print("Line 2 length:", len(best_line2))

print()


# ============================================================
# PARSE LINE 1
# ============================================================

document_code = best_line1[0:2]

issuing_country = best_line1[2:5]

name_field = best_line1[5:44]


# ============================================================
# NAME EXTRACTION
# ============================================================

surname = ""

given_name = ""


if "<<" in name_field:

    parts = name_field.split(
        "<<",
        1
    )

    surname = parts[0]

    given_name = parts[1]


else:

    # Fallback for corrupted separator
    #
    # Example:
    # ATTHI<X<MADHAVI

    name_field_clean = name_field

    # Known MRZ separator variants
    name_field_clean = re.sub(
        r"<X<",
        "<<",
        name_field_clean
    )

    name_field_clean = re.sub(
        r"<I<",
        "<<",
        name_field_clean
    )


    if "<<" in name_field_clean:

        parts = name_field_clean.split(
            "<<",
            1
        )

        surname = parts[0]

        given_name = parts[1]


# Remove filler characters

surname = surname.replace(
    "<",
    " "
)

given_name = given_name.replace(
    "<",
    " "
)


# Remove repeated spaces

surname = re.sub(
    r"\s+",
    " ",
    surname
).strip()


given_name = re.sub(
    r"\s+",
    " ",
    given_name
).strip()


# ============================================================
# PARSE LINE 2
# ============================================================

passport_number_raw = best_line2[0:9]

passport_number_check = best_line2[9]

nationality = best_line2[10:13]

date_of_birth_raw = best_line2[13:19]

date_of_birth_check = best_line2[19]

sex = best_line2[20]

date_of_expiry_raw = best_line2[21:27]

date_of_expiry_check = best_line2[27]

optional_data = best_line2[28:42]

overall_check = best_line2[43]


# ============================================================
# CLEAN FIELDS
# ============================================================

passport_number = passport_number_raw.replace(
    "<",
    ""
)


nationality = nationality.replace(
    "<",
    ""
)


optional_data = optional_data.replace(
    "<",
    ""
)


# ============================================================
# DATE CONVERSION
# ============================================================

def format_mrz_date(value):

    if not re.fullmatch(
        r"\d{6}",
        value
    ):

        return None


    year = int(
        value[0:2]
    )

    month = value[2:4]

    day = value[4:6]


    # For your project:
    #
    # 00-29 -> 2000-2029
    # 30-99 -> 1930-1999

    if year <= 29:

        full_year = 2000 + year

    else:

        full_year = 1900 + year


    return (
        f"{full_year:04d}-"
        f"{month}-"
        f"{day}"
    )


date_of_birth = format_mrz_date(
    date_of_birth_raw
)


date_of_expiry = format_mrz_date(
    date_of_expiry_raw
)


# ============================================================
# VALIDATION
# ============================================================

valid_passport_number = check_digit_valid(
    passport_number_raw,
    passport_number_check
)


valid_date_of_birth = check_digit_valid(
    date_of_birth_raw,
    date_of_birth_check
)


valid_date_of_expiry = check_digit_valid(
    date_of_expiry_raw,
    date_of_expiry_check
)


# ============================================================
# OVERALL CHECK DIGIT
# ============================================================

overall_check_data = (
    best_line2[0:10]
    +
    best_line2[13:20]
    +
    best_line2[21:28]
    +
    best_line2[28:43]
)


valid_overall_check_digit = check_digit_valid(
    overall_check_data,
    overall_check
)


# ============================================================
# FIELD FORMAT VALIDATION
# ============================================================

document_code_valid = (
    document_code == "P<"
)


issuing_country_valid = bool(
    re.fullmatch(
        r"[A-Z]{3}",
        issuing_country
    )
)


passport_number_format_valid = bool(
    re.fullmatch(
        r"[A-Z0-9]{6,9}",
        passport_number
    )
)


nationality_valid = bool(
    re.fullmatch(
        r"[A-Z]{3}",
        nationality
    )
)


dob_format_valid = bool(
    re.fullmatch(
        r"\d{6}",
        date_of_birth_raw
    )
)


expiry_format_valid = bool(
    re.fullmatch(
        r"\d{6}",
        date_of_expiry_raw
    )
)


sex_valid = sex in [
    "M",
    "F",
    "X",
    "<"
]


# ============================================================
# FINAL MRZ VALIDITY
# ============================================================

mrz_valid = (
    document_code_valid
    and
    issuing_country_valid
    and
    passport_number_format_valid
    and
    nationality_valid
    and
    dob_format_valid
    and
    expiry_format_valid
    and
    sex_valid
    and
    valid_passport_number
    and
    valid_date_of_birth
    and
    valid_date_of_expiry
    and
    valid_overall_check_digit
)


# ============================================================
# CONFIDENCE
# ============================================================

validation_checks = [

    valid_passport_number,

    valid_date_of_birth,

    valid_date_of_expiry,

    valid_overall_check_digit
]


valid_count = sum(
    validation_checks
)


mrz_confidence = round(
    (
        valid_count
        /
        len(validation_checks)
    )
    * 100,
    2
)


# ============================================================
# OCR DATA COMPARISON
# ============================================================

ocr_extracted = ocr_data.get(
    "extracted_data",
    {}
)


ocr_passport_number = ocr_extracted.get(
    "passport_number"
)


ocr_surname = ocr_extracted.get(
    "surname"
)


ocr_given_name = ocr_extracted.get(
    "given_name"
)


# ============================================================
# COMPARISON NORMALIZATION
# ============================================================

def normalize_compare(value):

    if value is None:

        return ""


    value = str(value).upper()


    value = re.sub(
        r"[^A-Z0-9]",
        "",
        value
    )


    return value


# ============================================================
# PASSPORT NUMBER COMPARISON
# ============================================================

passport_match = False


if ocr_passport_number:

    passport_match = (
        normalize_compare(
            ocr_passport_number
        )
        ==
        normalize_compare(
            passport_number
        )
    )


# ============================================================
# SURNAME COMPARISON
# ============================================================

surname_match = False


if ocr_surname:

    surname_match = (
        normalize_compare(
            ocr_surname
        )
        ==
        normalize_compare(
            surname
        )
    )


# ============================================================
# GIVEN NAME COMPARISON
# ============================================================

given_name_match = False


if ocr_given_name:

    given_name_match = (
        normalize_compare(
            ocr_given_name
        )
        ==
        normalize_compare(
            given_name
        )
    )


# ============================================================
# BUILD JSON RESULT
# ============================================================

mrz_result = {

    "document_type":
        "Passport",

    "document_code":
        document_code,

    "issuing_country":
        issuing_country,

    "surname":
        surname,

    "given_name":
        given_name,

    "passport_number":
        passport_number,

    "nationality":
        nationality,

    "date_of_birth":
        date_of_birth,

    "sex":
        sex,

    "date_of_expiry":
        date_of_expiry,

    "optional_data":
        optional_data,

    "raw_mrz": {

        "line1":
            best_line1,

        "line2":
            best_line2
    },

    "validation": {

        "document_code_valid":
            document_code_valid,

        "issuing_country_valid":
            issuing_country_valid,

        "passport_number_format_valid":
            passport_number_format_valid,

        "nationality_valid":
            nationality_valid,

        "dob_format_valid":
            dob_format_valid,

        "expiry_format_valid":
            expiry_format_valid,

        "sex_valid":
            sex_valid,

        "valid_passport_number":
            valid_passport_number,

        "valid_date_of_birth":
            valid_date_of_birth,

        "valid_date_of_expiry":
            valid_date_of_expiry,

        "valid_overall_check_digit":
            valid_overall_check_digit,

        "mrz_valid":
            mrz_valid,

        "confidence":
            mrz_confidence
    },

    "ocr_comparison": {

        "passport_number": {

            "ocr":
                ocr_passport_number,

            "mrz":
                passport_number,

            "match":
                passport_match
        },

        "surname": {

            "ocr":
                ocr_surname,

            "mrz":
                surname,

            "match":
                surname_match
        },

        "given_name": {

            "ocr":
                ocr_given_name,

            "mrz":
                given_name,

            "match":
                given_name_match
        }
    }
}


# ============================================================
# SAVE JSON
# ============================================================

with open(
    MRZ_FILE,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        mrz_result,
        file,
        indent=4,
        ensure_ascii=False
    )


# ============================================================
# DISPLAY RESULT
# ============================================================

print()
print("=" * 70)
print("                       MRZ RESULT")
print("=" * 70)
print()

print(
    "Document Code    :",
    document_code
)

print(
    "Issuing Country  :",
    issuing_country
)

print(
    "Surname          :",
    surname
)

print(
    "Given Name       :",
    given_name
)

print(
    "Passport Number  :",
    passport_number
)

print(
    "Nationality      :",
    nationality
)

print(
    "Date of Birth    :",
    date_of_birth
)

print(
    "Sex              :",
    sex
)

print(
    "Date of Expiry   :",
    date_of_expiry
)

print()


# ============================================================
# VALIDATION RESULT
# ============================================================

print("=" * 70)
print("                     VALIDATION")
print("=" * 70)
print()


print(
    "Passport Number Check :",
    "✅" if valid_passport_number else "❌"
)


print(
    "DOB Check             :",
    "✅" if valid_date_of_birth else "❌"
)


print(
    "Expiry Check          :",
    "✅" if valid_date_of_expiry else "❌"
)


print(
    "Overall Check         :",
    "✅" if valid_overall_check_digit else "❌"
)


print()


print(
    "MRZ Confidence:",
    str(mrz_confidence) + "%"
)


print(
    "MRZ Valid:",
    "✅ YES" if mrz_valid else "❌ NO"
)


print()


# ============================================================
# OCR COMPARISON
# ============================================================

print("=" * 70)
print("                  OCR vs MRZ COMPARISON")
print("=" * 70)
print()


print(
    "Passport Number:",
    "✅ MATCH" if passport_match else "⚠️ DIFFERENT"
)


print(
    "Surname:",
    "✅ MATCH" if surname_match else "⚠️ DIFFERENT"
)


print(
    "Given Name:",
    "✅ MATCH" if given_name_match else "⚠️ DIFFERENT"
)


print()


# ============================================================
# SAVE LOCATION
# ============================================================

print("=" * 70)

print(
    "MRZ data saved to:"
)

print(
    MRZ_FILE
)

print("=" * 70)

print()