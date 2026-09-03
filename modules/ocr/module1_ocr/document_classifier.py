# ============================================================
# AI-BASED FAKE IDENTITY & DOCUMENT SCREENING SYSTEM
# MODULE 1: DOCUMENT CLASSIFIER
# ============================================================

import re


def classify_document(text):
    """
    Classifies a document based on OCR text keywords and structure.
    Returns: 'PASSPORT' | 'VISA' | 'NATIONAL_ID' | 'DRIVING_LICENSE' | 'PERMIT' | 'TRAVEL_AUTH' | 'UNKNOWN'
    """
    if not text:
        return "UNKNOWN"

    text = text.upper()

    # 1. Driving Licence
    if (
        "DRIVING LICENCE" in text
        or "DRIVING LICENSE" in text
        or "DRIVER LICENSE" in text
        or "DL NO" in text
        or "UNION OF INDIA DRIVING" in text
    ):
        return "DRIVING_LICENSE"

    # 2. National ID / Aadhaar
    if (
        "AADHAAR" in text
        or "UNIQUE IDENTIFICATION" in text
        or "IDENTITY CARD" in text
        or "NATIONAL ID" in text
        or "GOVERNMENT OF INDIA" in text and ("ENROLMENT" in text or "MERA AADHAAR" in text)
    ):
        return "NATIONAL_ID"

    # 3. Visa (Check before generic Passport because visas often contain 'Passport No.')
    if (
        "VISA TYPE" in text
        or "VISA/CLASS" in text
        or "ISSUING POST" in text
        or "CONTROL NUMBER" in text
        or "BEARER" in text and "VISA" in text
        or re.search(r"\bVISA\b", text)
        or re.search(r"\bVISUM\b", text)
    ):
        return "VISA"

    # 4. Travel Authorization (ESTA / eTA / Electronic Travel Authorization)
    if (
        "ELECTRONIC TRAVEL AUTHORIZATION" in text
        or "ESTA APPLICATION" in text
        or "AUTHORIZATION APPROVED" in text
        or "TRAVEL AUTHORIZATION" in text
        or "ETA APPLICATION" in text
    ):
        return "TRAVEL_AUTH"

    # 5. Permit (Residence / Work / Student)
    if (
        "RESIDENCE PERMIT" in text
        or "WORK PERMIT" in text
        or "ENTRY PERMIT" in text
        or "STAY PERMIT" in text
        or re.search(r"\bPERMIT\b", text)
    ):
        return "PERMIT"

    # 6. Passport
    if (
        "PASSPORT" in text
        or "REPUBLIC OF" in text
        or "TRAVEL DOCUMENT" in text
        or "P<" in text
    ):
        return "PASSPORT"

    return "UNKNOWN"