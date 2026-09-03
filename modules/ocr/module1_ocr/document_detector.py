import cv2
import pytesseract
import os
import sys

# ============================================================
# TESSERACT CONFIGURATION
# ============================================================

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

# ============================================================
# IMAGE PATH
# ============================================================

IMAGE_PATH = os.path.join(
    "input",
    "passport.jpg"
)

print(f"Using image: {IMAGE_PATH}")


# ============================================================
# CHECK IMAGE
# ============================================================

if not os.path.exists(IMAGE_PATH):
    print("❌ Image not found.")
    sys.exit(1)

image = cv2.imread(IMAGE_PATH)

if image is None:
    print("❌ Could not read image.")
    sys.exit(1)


# ============================================================
# OCR
# ============================================================

gray = cv2.cvtColor(
    image,
    cv2.COLOR_BGR2GRAY
)

gray = cv2.resize(
    gray,
    None,
    fx=2,
    fy=2,
    interpolation=cv2.INTER_CUBIC
)

text = pytesseract.image_to_string(
    gray,
    config="--oem 3 --psm 6"
)

text = text.upper()


# ============================================================
# DOCUMENT DETECTION
# ============================================================

document_type = "UNKNOWN"


# ------------------------------------------------------------
# PASSPORT
# ------------------------------------------------------------

if (
    "PASSPORT" in text
    or "REPUBLIC OF INDIA" in text
    or "P<" in text
):
    document_type = "PASSPORT"


# ------------------------------------------------------------
# VISA
# ------------------------------------------------------------

elif (
    "VISA" in text
    or "ENTRY PERMIT" in text
):
    document_type = "VISA"


# ------------------------------------------------------------
# DRIVING LICENCE
# ------------------------------------------------------------

elif (
    "DRIVING LICENCE" in text
    or "DRIVING LICENSE" in text
    or "DL NO" in text
):
    document_type = "DRIVING_LICENCE"


# ------------------------------------------------------------
# NATIONAL ID
# ------------------------------------------------------------

elif (
    "AADHAAR" in text
    or "IDENTITY CARD" in text
    or "NATIONAL ID" in text
):
    document_type = "NATIONAL_ID"


# ------------------------------------------------------------
# PERMIT
# ------------------------------------------------------------

elif (
    "PERMIT" in text
    or "RESIDENCE PERMIT" in text
    or "WORK PERMIT" in text
):
    document_type = "PERMIT"


# ============================================================
# RESULT
# ============================================================

print("\n========== DOCUMENT DETECTION ==========\n")

print(f"Document Type: {document_type}")

print("\n=========================================")


# ============================================================
# EXIT STATUS
# ============================================================

if document_type == "UNKNOWN":
    print("⚠️ Document type could not be detected.")
else:
    print("✅ Document type detected successfully.")