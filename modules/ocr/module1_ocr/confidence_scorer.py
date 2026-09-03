# ============================================================
# AI-BASED FAKE IDENTITY & DOCUMENT SCREENING SYSTEM
# MODULE 1: CONFIDENCE SCORER & QUALITY ASSESSMENT
# ============================================================


def calculate_field_confidences(identity, document, verification, quality_report=None):
    """
    Assigns calibrated per-field confidence scores (0-100%) based on:
      - Field presence and pattern plausibility
      - MRZ checksum validation
      - Cross-field consistency (Visual OCR vs MRZ)
      - Image quality / blur penalty
    """
    quality_score = quality_report.get("quality_score", 100.0) if quality_report else 100.0
    quality_penalty = 1.0 if quality_score >= 70.0 else (quality_score / 100.0)

    field_scores = {}
    comps = verification.get("field_comparisons", {}) if verification else {}
    mrz_valid = verification.get("mrz_valid", False) if verification else False

    # 1. Identity Fields
    for field, val in (identity or {}).items():
        if not val or str(val).strip() in ["N/A", "None", ""]:
            field_scores[field] = 0.0
            continue

        # Base score for valid extracted string
        base = 85.0

        # Check cross-check comparison if available
        comp_res = comps.get(field)
        if comp_res == "MATCH":
            base = 100.0
        elif comp_res == "DIFFERENT":
            base = 40.0
        elif comp_res == "MISSING_OCR":
            base = 75.0 if mrz_valid else 50.0

        # Quality modulation
        score = round(base * quality_penalty, 2)
        field_scores[field] = max(10.0, min(100.0, score))

    # 2. Document Fields
    for field, val in (document or {}).items():
        if not val or str(val).strip() in ["N/A", "None", ""]:
            field_scores[field] = 0.0
            continue

        base = 80.0
        if field in ["document_number", "passport_number"]:
            if mrz_valid:
                base = 100.0
            elif comps.get("passport_number") == "MATCH":
                base = 95.0
            elif comps.get("passport_number") == "DIFFERENT":
                base = 40.0

        if field in ["date_of_expiry", "date_of_issue"]:
            if comps.get(field) == "MATCH":
                base = 95.0
            elif comps.get(field) == "DIFFERENT":
                base = 45.0

        score = round(base * quality_penalty, 2)
        field_scores[field] = max(10.0, min(100.0, score))

    return field_scores


def should_require_manual_review(confidence_score, verification=None, quality_report=None, identity=None, document=None):
    """
    Evaluates whether a document requires human operator manual review.
    
    Trigger Conditions:
      1. Overall extraction confidence score < 75.0%
      2. Any cross-check field status is 'DIFFERENT' (inconsistency detected)
      3. Image quality is 'BLURRY' or quality_score < 50.0%
      4. MRZ is available but checksum fails
      5. Mandatory primary identity fields (full_name, document_number) are missing
    """
    reasons = []

    # Condition 1: Overall confidence
    if confidence_score < 75.0:
        reasons.append(f"Overall confidence score is low ({confidence_score}%)")

    # Condition 2: Field Inconsistencies
    comps = verification.get("field_comparisons", {}) if verification else {}
    for f, res in comps.items():
        if res == "DIFFERENT":
            reasons.append(f"Cross-check mismatch on field: {f}")

    # Condition 3: Quality
    if quality_report:
        if quality_report.get("blur_status") == "BLURRY":
            reasons.append("Image is noticeably blurry")
        if quality_report.get("quality_score", 100.0) < 50.0:
            reasons.append("Image quality score is below acceptable threshold")

    # Condition 4: MRZ Checksum Failure
    if verification and verification.get("mrz_available") and not verification.get("mrz_valid"):
        reasons.append("MRZ check digit checksum validation failed")

    # Condition 5: Critical Fields Missing
    if identity and not identity.get("full_name"):
        reasons.append("Primary identity full_name could not be extracted")
    if document and not document.get("document_number"):
        reasons.append("Primary document_number could not be extracted")

    return len(reasons) > 0, reasons


def calculate_confidence(mrz_data, consistency):
    """
    Legacy helper for calculating overall MRZ confidence.
    """
    score = 0
    mrz_score = mrz_data.get("mrz_valid_score", 0)

    if mrz_score >= 80:
        score += 40
    elif mrz_score >= 60:
        score += 30
    elif mrz_score >= 40:
        score += 20
    else:
        score += 10

    if mrz_data.get("valid_passport_number"):
        score += 20
    if mrz_data.get("valid_date_of_birth"):
        score += 15
    if mrz_data.get("valid_date_of_expiry"):
        score += 15

    if consistency.get("nationality_match") is True:
        score += 5
    if consistency.get("gender_match") is True:
        score += 5

    score = min(score, 100)
    level = "HIGH" if score >= 80 else ("MEDIUM" if score >= 55 else "LOW")

    return {
        "score": score,
        "level": level
    }