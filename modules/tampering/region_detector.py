import cv2
import numpy as np


def detect_suspicious_regions(
    ela_path,
    output_path,
    threshold=30,
    min_area=20
):
    """
    Detect bright/anomalous regions in an ELA image
    and highlight candidate regions on the ELA image.

    These are TAMPERING CANDIDATES, not proof of forgery.
    """

    image = cv2.imread(ela_path)

    if image is None:
        raise FileNotFoundError(
            f"Could not open ELA image: {ela_path}"
        )

    # Convert ELA image to grayscale
    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    # Find pixels above the ELA threshold
    _, mask = cv2.threshold(
        gray,
        threshold,
        255,
        cv2.THRESH_BINARY
    )

    # Find connected suspicious regions
    contours, _ = cv2.findContours(
        mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    result = image.copy()

    regions = []
    suspicious_area = 0

    for contour in contours:

        area = cv2.contourArea(contour)

        # Ignore very tiny noise
        if area < min_area:
            continue

        x, y, w, h = cv2.boundingRect(contour)

        regions.append({
            "x": int(x),
            "y": int(y),
            "width": int(w),
            "height": int(h),
            "area": round(float(area), 2)
        })

        suspicious_area += area

        # Draw red rectangle
        cv2.rectangle(
            result,
            (x, y),
            (x + w, y + h),
            (0, 0, 255),
            3
        )

    total_area = image.shape[0] * image.shape[1]

    suspicious_percentage = (
        suspicious_area / total_area
    ) * 100

    # Add title to output image
    cv2.putText(
        result,
        "Potential Suspicious Regions",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 0, 255),
        2
    )

    # Save result
    cv2.imwrite(
        output_path,
        result
    )

    return {
        "region_count": len(regions),
        "suspicious_percentage":
            round(suspicious_percentage, 4),
        "regions": regions
    }