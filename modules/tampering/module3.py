from pathlib import Path

from ela import perform_ela
from ela_score import calculate_ela_score
from metadata_analysis import analyze_metadata
from region_detector import detect_suspicious_regions
from photo_analysis import analyze_photo
from risk_engine import calculate_combined_risk


# ============================================================
# MODULE 3 - AI DOCUMENT TAMPERING DETECTION
# ============================================================

def analyze_tampering(image_path):
    """
    Main Module 3 pipeline.

    Performs:
        1. ELA analysis
        2. Metadata analysis
        3. Suspicious-region detection
        4. Photo-region analysis
        5. Combined risk scoring

    Returns a complete analysis result.
    """

    image_path = str(image_path)

    # ========================================================
    # CHECK INPUT
    # ========================================================

    if not Path(image_path).exists():
        raise FileNotFoundError(
            f"Document not found: {image_path}"
        )

    # ========================================================
    # OUTPUT DIRECTORY
    # ========================================================

    output_dir = Path("outputs/module3")

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    # ========================================================
    # 1. ELA ANALYSIS
    # ========================================================

    ela_output = (
        output_dir /
        "ela_result.jpg"
    )

    perform_ela(
        image_path,
        str(ela_output)
    )

    ela_percentage = calculate_ela_score(
        str(ela_output)
    )

    # ========================================================
    # 2. METADATA ANALYSIS
    # ========================================================

    metadata = analyze_metadata(
        image_path
    )

    metadata_fields = (
        metadata["metadata_fields"]
    )

    # ========================================================
    # 3. SUSPICIOUS REGION DETECTION
    # ========================================================

    region_output = (
        output_dir /
        "suspicious_regions.jpg"
    )

    regions = detect_suspicious_regions(
        str(ela_output),
        str(region_output)
    )

    region_count = (
        regions["region_count"]
    )

    suspicious_percentage = (
        regions["suspicious_percentage"]
    )

    # ========================================================
    # 4. PHOTO REGION ANALYSIS
    # ========================================================

    photo_output_prefix = (
        output_dir /
        "photo"
    )

    photo = analyze_photo(
        image_path,
        str(photo_output_prefix)
    )

    photo_percentage = (
        photo["percentage"]
    )

    photo_score = (
        photo["photo_score"]
    )

    photo_result = (
        photo["result"]
    )

    # ========================================================
    # 5. COMBINED RISK ENGINE
    # ========================================================

    risk = calculate_combined_risk(
        ela_percentage,
        metadata_fields,
        region_count,
        suspicious_percentage,
        photo_score
    )

    # ========================================================
    # FINAL VALUES
    # ========================================================

    final_score = risk["final_score"]

    risk_level = risk["risk_level"]

    # ========================================================
    # SCREENING MESSAGE
    # ========================================================

    if risk_level == "HIGH":

        screening_message = (
            "POTENTIAL TAMPERING DETECTED"
        )

    elif risk_level == "MEDIUM":

        screening_message = (
            "DOCUMENT REQUIRES MANUAL REVIEW"
        )

    else:

        screening_message = (
            "NO STRONG TAMPERING INDICATORS"
        )

    # ========================================================
    # RETURN COMPLETE RESULT
    # ========================================================

    return {

        "image": image_path,

        # ----------------------------------------------------
        # ELA
        # ----------------------------------------------------

        "ela": {

            "anomaly": ela_percentage,

            "risk": risk["ela_score"],

            "output": str(
                ela_output
            )
        },

        # ----------------------------------------------------
        # METADATA
        # ----------------------------------------------------

        "metadata": {

            "fields": metadata_fields,

            "risk": risk["metadata_score"]
        },

        # ----------------------------------------------------
        # REGIONS
        # ----------------------------------------------------

        "regions": {

            "count": region_count,

            "area": suspicious_percentage,

            "risk": risk["region_score"],

            "output": str(
                region_output
            )
        },

        # ----------------------------------------------------
        # PHOTO
        # ----------------------------------------------------

        "photo": {

            "inconsistency": photo_percentage,

            "risk": photo_score,

            "result": photo_result,

            "output": photo["ela_output"]
        },

        # ----------------------------------------------------
        # FINAL
        # ----------------------------------------------------

        "final_score": final_score,

        "risk_level": risk_level,

        "screening_message": screening_message
    }


# ============================================================
# STANDALONE TEST
# ============================================================

if __name__ == "__main__":

    # ========================================================
    # TEST DOCUMENT
    # ========================================================
    #
    # Change ONLY this path when testing manually.
    #
    # ========================================================

    IMAGE = (
        "test_documents/tampered/"
        "tampered2.jpg"
    )

    # ========================================================
    # HEADER
    # ========================================================

    print()
    print("================================================")
    print("       MODULE 3 TAMPERING TEST")
    print("================================================")

    print()
    print("Document:", IMAGE)

    print("----------------------------------------")

    # ========================================================
    # RUN ANALYSIS
    # ========================================================

    try:

        result = analyze_tampering(
            IMAGE
        )

    except Exception as error:

        print()
        print("❌ ANALYSIS FAILED")
        print("--------------------------------")
        print(error)
        print("========================================")

        raise SystemExit(1)

    # ========================================================
    # ELA
    # ========================================================

    print(
        "ELA anomaly:",
        result["ela"]["anomaly"],
        "%"
    )

    print(
        "ELA risk:",
        result["ela"]["risk"],
        "/100"
    )

    # ========================================================
    # METADATA
    # ========================================================

    print(
        "Metadata fields:",
        result["metadata"]["fields"]
    )

    print(
        "Metadata risk:",
        result["metadata"]["risk"],
        "/100"
    )

    # ========================================================
    # REGIONS
    # ========================================================

    print(
        "Suspicious regions:",
        result["regions"]["count"]
    )

    print(
        "Suspicious area:",
        result["regions"]["area"],
        "%"
    )

    print(
        "Region risk:",
        result["regions"]["risk"],
        "/100"
    )

    # ========================================================
    # PHOTO
    # ========================================================

    print(
        "Photo inconsistency:",
        result["photo"]["inconsistency"],
        "%"
    )

    print(
        "Photo risk:",
        result["photo"]["risk"],
        "/100"
    )

    print(
        "Photo finding:",
        result["photo"]["result"]
    )

    # ========================================================
    # FINAL RISK
    # ========================================================

    print("----------------------------------------")

    print(
        "FINAL RISK:",
        result["final_score"],
        "/100"
    )

    print(
        "RISK LEVEL:",
        result["risk_level"]
    )

    print("----------------------------------------")

    if result["risk_level"] == "HIGH":

        print(
            "⚠️ POTENTIAL TAMPERING DETECTED"
        )

    elif result["risk_level"] == "MEDIUM":

        print(
            "⚠️ DOCUMENT REQUIRES MANUAL REVIEW"
        )

    else:

        print(
            "✓ NO STRONG TAMPERING INDICATORS"
        )

    # ========================================================
    # OUTPUTS
    # ========================================================

    print("----------------------------------------")

    print(
        "ELA output:",
        result["ela"]["output"]
    )

    print(
        "Suspicious regions output:",
        result["regions"]["output"]
    )

    print(
        "Photo ELA output:",
        result["photo"]["output"]
    )

    print("========================================")