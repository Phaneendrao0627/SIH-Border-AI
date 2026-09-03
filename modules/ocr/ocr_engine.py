# ============================================================
# AI-BASED FAKE IDENTITY & DOCUMENT SCREENING SYSTEM
# OCR ENGINE
# ============================================================

import cv2
import pytesseract
import json
import re
import os
import sys
from datetime import datetime


# ============================================================
# CONFIGURATION
# ============================================================

TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

INPUT_FOLDER = "input"
OUTPUT_FOLDER = "output"

OCR_OUTPUT_FILE = os.path.join(
    OUTPUT_FOLDER,
    "ocr_data.json"
)


# ============================================================
# TESSERACT SETUP
# ============================================================

pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


# ============================================================
# HEADER
# ============================================================

print()
print("=" * 70)
print("       AI-BASED DOCUMENT SCREENING SYSTEM")
print("                     OCR ENGINE")
print("=" * 70)
print()


# ============================================================
# INPUT IMAGE
# ============================================================

if len(sys.argv) > 1:

    image_path = sys.argv[1]

else:

    image_path = os.path.join(
        INPUT_FOLDER,
        "passport.jpg"
    )


print("[1] Input Image")
print("-" * 70)
print("Image:", image_path)
print()


# ============================================================
# CHECK TESSERACT
# ============================================================

print("[2] Tesseract Check")
print("-" * 70)

if not os.path.exists(TESSERACT_PATH):

    print("❌ Tesseract not found.")
    print()
    print("Expected location:")
    print(TESSERACT_PATH)

    sys.exit(1)

print("✅ Tesseract found")
print()


# ============================================================
# CHECK IMAGE
# ============================================================

print("[3] Image Check")
print("-" * 70)

if not os.path.exists(image_path):

    print("❌ Image not found:")
    print(image_path)

    sys.exit(1)

print("✅ Image found")
print()


# ============================================================
# LOAD IMAGE
# ============================================================

print("[4] Loading Image")
print("-" * 70)

image = cv2.imread(image_path)

if image is None:

    print("❌ Unable to read image")

    sys.exit(1)

print("✅ Image loaded")
print()


# ============================================================
# IMAGE INFORMATION
# ============================================================

height, width, channels = image.shape

print("[5] Image Information")
print("-" * 70)

print("Width    :", width)
print("Height   :", height)
print("Channels :", channels)

print()


# ============================================================
# CREATE OUTPUT DIRECTORY
# ============================================================

os.makedirs(
    OUTPUT_FOLDER,
    exist_ok=True
)


# ============================================================
# GRAYSCALE
# ============================================================

print("[6] Grayscale Conversion")
print("-" * 70)

gray = cv2.cvtColor(
    image,
    cv2.COLOR_BGR2GRAY
)

print("✅ Completed")
print()


# ============================================================
# RESIZE
# ============================================================

print("[7] Image Resizing")
print("-" * 70)

gray_resized = cv2.resize(
    gray,
    None,
    fx=2,
    fy=2,
    interpolation=cv2.INTER_CUBIC
)

print("✅ Image resized 2x")
print()


# ============================================================
# NOISE REDUCTION
# ============================================================

print("[8] Noise Reduction")
print("-" * 70)

blurred = cv2.GaussianBlur(
    gray_resized,
    (3, 3),
    0
)

print("✅ Gaussian blur applied")
print()


# ============================================================
# OTSU THRESHOLD
# ============================================================

print("[9] OTSU Threshold")
print("-" * 70)

threshold_image = cv2.threshold(
    blurred,
    0,
    255,
    cv2.THRESH_BINARY + cv2.THRESH_OTSU
)[1]

print("✅ Threshold created")
print()


# ============================================================
# ADAPTIVE THRESHOLD
# ============================================================

print("[10] Adaptive Threshold")
print("-" * 70)

adaptive_image = cv2.adaptiveThreshold(
    gray_resized,
    255,
    cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
    cv2.THRESH_BINARY,
    31,
    11
)

print("✅ Adaptive threshold created")
print()


# ============================================================
# MORPHOLOGICAL PROCESSING
# ============================================================

print("[11] Morphological Processing")
print("-" * 70)

kernel = cv2.getStructuringElement(
    cv2.MORPH_RECT,
    (2, 2)
)

morph_image = cv2.morphologyEx(
    threshold_image,
    cv2.MORPH_OPEN,
    kernel
)

print("✅ Morphological processing completed")
print()


# ============================================================
# SAVE PROCESSED IMAGE
# ============================================================

processed_image_path = os.path.join(
    OUTPUT_FOLDER,
    "processed_document.png"
)

cv2.imwrite(
    processed_image_path,
    threshold_image
)

print("Processed image saved:")
print(processed_image_path)
print()


# ============================================================
# OCR FUNCTION
# ============================================================

def run_ocr(img, psm):

    try:

        config = f"--psm {psm}"

        text = pytesseract.image_to_string(
            img,
            config=config
        )

        return text

    except Exception as error:

        print("OCR error:", error)

        return ""


# ============================================================
# OCR PASS 1
# ============================================================

print("[12] OCR Pass 1")
print("-" * 70)

text_pass_1 = run_ocr(
    gray_resized,
    6
)

print("✅ Pass 1 completed")
print()


# ============================================================
# OCR PASS 2
# ============================================================

print("[13] OCR Pass 2")
print("-" * 70)

text_pass_2 = run_ocr(
    threshold_image,
    6
)

print("✅ Pass 2 completed")
print()


# ============================================================
# OCR PASS 3
# ============================================================

print("[14] OCR Pass 3")
print("-" * 70)

text_pass_3 = run_ocr(
    gray_resized,
    11
)

print("✅ Pass 3 completed")
print()


# ============================================================
# OCR PASS 4
# ============================================================

print("[15] OCR Pass 4")
print("-" * 70)

text_pass_4 = run_ocr(
    adaptive_image,
    11
)

print("✅ Pass 4 completed")
print()


# ============================================================
# COMBINE OCR
# ============================================================

raw_text = (
    text_pass_1
    + "\n"
    + text_pass_2
    + "\n"
    + text_pass_3
    + "\n"
    + text_pass_4
)


# ============================================================
# NORMALIZE OCR TEXT
# ============================================================

def normalize_text(text):

    if not text:
        return ""

    text = text.replace(
        "\r",
        "\n"
    )

    text = re.sub(
        r"[ \t]+",
        " ",
        text
    )

    text = re.sub(
        r"\n+",
        "\n",
        text
    )

    return text.strip()


normalized_text = normalize_text(
    raw_text
)


# ============================================================
# CLEAN VALUE
# ============================================================

def clean_value(value):

    if value is None:

        return None

    value = value.strip()

    value = re.sub(
        r"\s+",
        " ",
        value
    )

    return value.strip()


# ============================================================
# FIND FIRST MATCH
# ============================================================

def find_first(patterns, text):

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            return clean_value(
                match.group(1)
            )

    return None


# ============================================================
# DATE NORMALIZATION
# ============================================================

def normalize_date(value):

    if not value:

        return None

    value = value.strip()

    value = value.replace(
        ".",
        "/"
    )

    value = value.replace(
        "-",
        "/"
    )

    return value


# ============================================================
# DOCUMENT TYPE DETECTION
# ============================================================

text_upper = normalized_text.upper()

document_type = "Unknown"


# ============================================================
# NATIONAL ID DETECTION
# ============================================================

if (
    "AADHAAR" in text_upper
    or
    "UNIQUE IDENTIFICATION AUTHORITY OF INDIA"
    in text_upper
):

    document_type = "National ID"


# ============================================================
# DRIVING LICENCE DETECTION
# ============================================================

elif (
    "DRIVING LICENCE" in text_upper
    or
    "DRIVING LICENSE" in text_upper
):

    document_type = "Driving Licence"


# ============================================================
# VISA DETECTION
# ============================================================

elif (
    "VISA TYPE" in text_upper
    or
    "VISA/CLASS" in text_upper
    or
    "ISSUING POST NAME" in text_upper
):

    document_type = "Visa"


# ============================================================
# PERMIT DETECTION
# ============================================================

elif "PERMIT" in text_upper:

    document_type = "Permit"


# ============================================================
# PASSPORT DETECTION
# ============================================================

elif (
    "PASSPORT" in text_upper
    or
    "REPUBLIC OF INDIA" in text_upper
    or
    re.search(r"\bP<[A-Z]{3}", text_upper)
):

    document_type = "Passport"


print("[16] Document Detection")
print("-" * 70)

print("Detected document type:", document_type)

print()


# ============================================================
# EXTRACTED DATA
# ============================================================

extracted_data = {}


# ============================================================
# PASSPORT EXTRACTION
# ============================================================

if document_type == "Passport":

    print("[17] Passport Extraction")
    print("-" * 70)


    passport_number = find_first(
        [
            r"Passport\s*(?:No|Number)\s*[:\-]?\s*([A-Z0-9]{6,12})",
            r"Passport\s*[:\-]?\s*([A-Z0-9]{6,12})"
        ],
        normalized_text
    )


    surname = find_first(
        [
            r"Surname\s*[:\-]?\s*([A-Z][A-Z ]+)"
        ],
        normalized_text
    )


    given_name = find_first(
        [
            r"Given\s*Name[s]?\s*[:\-]?\s*([A-Z][A-Z ]+)"
        ],
        normalized_text
    )


    nationality = find_first(
        [
            r"Nationality\s*[:\-]?\s*([A-Z]{3,})"
        ],
        normalized_text
    )


    date_of_birth = find_first(
        [
            r"Date\s*of\s*Birth\s*[:\-]?\s*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})"
        ],
        normalized_text
    )


    gender = find_first(
        [
            r"Sex\s*[:\-]?\s*([MF])"
        ],
        normalized_text
    )


    date_of_issue = find_first(
        [
            r"Date\s*of\s*Issue\s*[:\-]?\s*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})"
        ],
        normalized_text
    )


    date_of_expiry = find_first(
        [
            r"Date\s*of\s*Expiry\s*[:\-]?\s*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})"
        ],
        normalized_text
    )


    place_of_birth = find_first(
        [
            r"Place\s*of\s*Birth\s*[:\-]?\s*([A-Z][A-Z ]+)"
        ],
        normalized_text
    )


    place_of_issue = find_first(
        [
            r"Place\s*of\s*Issue\s*[:\-]?\s*([A-Z][A-Z ]+)"
        ],
        normalized_text
    )


    extracted_data = {

        "passport_number":
            passport_number,

        "surname":
            surname,

        "given_name":
            given_name,

        "nationality":
            nationality,

        "date_of_birth":
            normalize_date(date_of_birth),

        "gender":
            gender,

        "date_of_issue":
            normalize_date(date_of_issue),

        "date_of_expiry":
            normalize_date(date_of_expiry),

        "place_of_birth":
            place_of_birth,

        "place_of_issue":
            place_of_issue
    }


# ============================================================
# VISA EXTRACTION
# ============================================================

elif document_type == "Visa":

    print("[17] Visa Extraction")
    print("-" * 70)


    issuing_post = find_first(
        [
            r"Issuing\s*Post\s*Name\s*[:\-]?\s*([A-Z][A-Z ]+)"
        ],
        normalized_text
    )


    surname = find_first(
        [
            r"Surname\s*[:\-]?\s*([A-Z][A-Z ]+)"
        ],
        normalized_text
    )


    given_name = find_first(
        [
            r"Given\s*Name[s]?\s*[:\-]?\s*([A-Z][A-Z ]+)"
        ],
        normalized_text
    )


    passport_number = find_first(
        [
            r"Passport\s*Number\s*[:\-]?\s*([A-Z0-9]+)",
            r"Passport\s*No\s*[:\-]?\s*([A-Z0-9]+)"
        ],
        normalized_text
    )


    visa_type = find_first(
        [
            r"Visa\s*Type\s*[/]?\s*Class\s*[:\-]?\s*([A-Z0-9]+)",
            r"Visa\s*Type\s*[:\-]?\s*([A-Z0-9]+)"
        ],
        normalized_text
    )


    nationality = find_first(
        [
            r"Nationality\s*[:\-]?\s*([A-Z]{3,})"
        ],
        normalized_text
    )


    sex = find_first(
        [
            r"Sex\s*[:\-]?\s*([MF])"
        ],
        normalized_text
    )


    birth_date = find_first(
        [
            r"Birth\s*Date\s*[:\-]?\s*([0-9A-Z]+)"
        ],
        normalized_text
    )


    issue_date = find_first(
        [
            r"Issue\s*Date\s*[:\-]?\s*([0-9A-Z]+)"
        ],
        normalized_text
    )


    expiration_date = find_first(
        [
            r"Expiration\s*Date\s*[:\-]?\s*([0-9A-Z]+)",
            r"Expiry\s*Date\s*[:\-]?\s*([0-9A-Z]+)"
        ],
        normalized_text
    )


    extracted_data = {

        "issuing_post":
            issuing_post,

        "surname":
            surname,

        "given_name":
            given_name,

        "passport_number":
            passport_number,

        "visa_type":
            visa_type,

        "nationality":
            nationality,

        "sex":
            sex,

        "birth_date":
            birth_date,

        "issue_date":
            issue_date,

        "expiration_date":
            expiration_date
    }


# ============================================================
# NATIONAL ID EXTRACTION
# ============================================================

elif document_type == "National ID":

    print("[17] National ID Extraction")
    print("-" * 70)


    id_number = find_first(
        [
            r"\b(\d{4}\s?\d{4}\s?\d{4})\b"
        ],
        normalized_text
    )


    if id_number:

        id_number = re.sub(
            r"\s+",
            " ",
            id_number
        )


    gender = None


    if re.search(
        r"\bMALE\b",
        text_upper
    ):

        gender = "M"


    elif re.search(
        r"\bFEMALE\b",
        text_upper
    ):

        gender = "F"


    full_name = find_first(
        [
            r"Name\s*[:\-]?\s*([A-Z][A-Z ]+)"
        ],
        normalized_text
    )


    extracted_data = {

        "id_number":
            id_number,

        "full_name":
            full_name,

        "gender":
            gender
    }


# ============================================================
# DRIVING LICENCE EXTRACTION
# ============================================================

elif document_type == "Driving Licence":

    print("[17] Driving Licence Extraction")
    print("-" * 70)


    licence_number = find_first(
        [
            r"(?:DL|Licence|License)\s*(?:No|Number)?\s*[:\-]?\s*([A-Z0-9\-]+)"
        ],
        normalized_text
    )


    name = find_first(
        [
            r"Name\s*[:\-]?\s*([A-Z][A-Z ]+)"
        ],
        normalized_text
    )


    date_of_birth = find_first(
        [
            r"Date\s*of\s*Birth\s*[:\-]?\s*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})"
        ],
        normalized_text
    )


    expiry_date = find_first(
        [
            r"Validity\s*[:\-]?\s*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})"
        ],
        normalized_text
    )


    extracted_data = {

        "licence_number":
            licence_number,

        "name":
            name,

        "date_of_birth":
            normalize_date(date_of_birth),

        "expiry_date":
            normalize_date(expiry_date)
    }


# ============================================================
# PERMIT EXTRACTION
# ============================================================

elif document_type == "Permit":

    print("[17] Permit Extraction")
    print("-" * 70)


    permit_number = find_first(
        [
            r"Permit\s*(?:No|Number)?\s*[:\-]?\s*([A-Z0-9\-]+)"
        ],
        normalized_text
    )


    name = find_first(
        [
            r"Name\s*[:\-]?\s*([A-Z][A-Z ]+)"
        ],
        normalized_text
    )


    extracted_data = {

        "permit_number":
            permit_number,

        "name":
            name
    }


# ============================================================
# UNKNOWN DOCUMENT
# ============================================================

else:

    print("[17] Unknown Document")
    print("-" * 70)


    extracted_data = {

        "message":
            "Document type could not be detected",

        "raw_detected_text":
            normalized_text[:1000]
    }


# ============================================================
# CALCULATE BASIC CONFIDENCE
# ============================================================

def calculate_confidence(data):

    if not data:

        return 0


    total_fields = len(data)

    valid_fields = 0


    for key, value in data.items():

        if value:

            valid_fields += 1


    if total_fields == 0:

        return 0


    confidence = (
        valid_fields /
        total_fields
    ) * 100


    return round(
        confidence,
        2
    )


confidence = calculate_confidence(
    extracted_data
)


# ============================================================
# OCR METADATA
# ============================================================

metadata = {

    "processed_at":
        datetime.now().isoformat(),

    "input_file":
        image_path,

    "image_width":
        width,

    "image_height":
        height,

    "ocr_engine":
        "Tesseract",

    "preprocessing":
        [
            "Grayscale",
            "2x Resize",
            "Gaussian Blur",
            "Otsu Threshold",
            "Adaptive Threshold",
            "Morphological Processing"
        ],

    "ocr_passes":
        4,

    "confidence":
        confidence
}


# ============================================================
# FINAL OCR JSON
# ============================================================

ocr_data = {

    "document_type":
        document_type,

    "status":
        "OCR_COMPLETED",

    "metadata":
        metadata,
        # IMPORTANT FOR MRZ ENGINE
    "raw_text":
        raw_text,

    "normalized_text":
        normalized_text,

    "extracted_data":
        extracted_data
}


# ============================================================
# SAVE OCR JSON
# ============================================================

print()
print("[18] Saving OCR Data")
print("-" * 70)


with open(
    OCR_OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        ocr_data,
        file,
        indent=4,
        ensure_ascii=False
    )


print("✅ OCR JSON saved")
print(OCR_OUTPUT_FILE)
print()


# ============================================================
# DISPLAY RESULT
# ============================================================

print("=" * 70)
print("                     OCR RESULT")
print("=" * 70)

print()

print(
    "Document Type:",
    document_type
)

print(
    "Confidence:",
    str(confidence) + "%"
)

print()

print("Extracted Data:")
print("-" * 70)

print(
    json.dumps(
        extracted_data,
        indent=4,
        ensure_ascii=False
    )
)

print()


# ============================================================
# RAW OCR PREVIEW
# ============================================================

print("=" * 70)
print("                   RAW OCR PREVIEW")
print("=" * 70)

print()

print(
    normalized_text[:3000]
)

print()


# ============================================================
# COMPLETION
# ============================================================

print("=" * 70)
print("                  OCR ENGINE COMPLETE")
print("=" * 70)

print()

print("Input  :", image_path)
print("Output :", OCR_OUTPUT_FILE)

print()

print("Next step:")
print("Run the MRZ engine for passport verification.")

print()