def calculate_ela_risk(ela_percentage):
    """
    Prototype ELA risk score.
    ELA is treated as one forensic indicator,
    not proof of tampering.
    """

    if ela_percentage < 0.25:
        return 10

    elif ela_percentage < 0.45:
        return 25

    elif ela_percentage < 0.70:
        return 45

    elif ela_percentage < 1.20:
        return 65

    else:
        return 75


def calculate_metadata_risk(metadata_fields):
    """
    Metadata is only a supporting indicator.
    Missing metadata does NOT mean a document is fake.
    """

    if metadata_fields == 0:
        return 0

    elif metadata_fields <= 2:
        return 10

    elif metadata_fields <= 5:
        return 20

    else:
        return 30


def calculate_region_risk(
    region_count,
    suspicious_percentage
):
    """
    Prototype suspicious-region risk.

    Region count alone is not enough because
    different image sizes can produce different
    numbers of candidate regions.
    """

    if suspicious_percentage < 0.25:
        return 10

    elif suspicious_percentage < 0.50:
        return 25

    elif suspicious_percentage < 1.00:
        return 45

    elif suspicious_percentage < 1.50:
        return 65

    else:
        return 75


def calculate_photo_risk(photo_score):
    """
    Photo-region risk supplied by photo_analysis.py.
    """

    return min(
        100,
        max(0, int(photo_score))
    )


def calculate_combined_risk(
    ela_percentage,
    metadata_fields,
    region_count=0,
    suspicious_percentage=0,
    photo_score=10
):
    """
    Combine multiple forensic indicators.

    Prototype weighting:

        ELA       = 40%
        Regions   = 20%
        Photo     = 30%
        Metadata  = 10%

    These are experimental prototype weights.
    """

    ela_score = calculate_ela_risk(
        ela_percentage
    )

    metadata_score = calculate_metadata_risk(
        metadata_fields
    )

    region_score = calculate_region_risk(
        region_count,
        suspicious_percentage
    )

    photo_risk = calculate_photo_risk(
        photo_score
    )

    final_score = round(
        (ela_score * 0.40)
        +
        (region_score * 0.20)
        +
        (photo_risk * 0.30)
        +
        (metadata_score * 0.10)
    )

    # Keep score between 0 and 100
    final_score = min(
        100,
        max(0, final_score)
    )

    if final_score >= 60:

        risk_level = "HIGH"

    elif final_score >= 30:

        risk_level = "MEDIUM"

    else:

        risk_level = "LOW"

    return {
        "ela_score": ela_score,
        "metadata_score": metadata_score,
        "region_score": region_score,
        "photo_score": photo_risk,
        "final_score": final_score,
        "risk_level": risk_level
    }