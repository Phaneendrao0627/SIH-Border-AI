# ============================================================
# AI-BASED FAKE IDENTITY & DOCUMENT SCREENING SYSTEM
# MODULE 1: IMAGE PREPROCESSING & QUALITY ASSESSMENT
# ============================================================

import os
import cv2
import numpy as np


def assess_image_quality(image):
    """
    Evaluates image sharpness, brightness, contrast, glare, and resolution.
    Returns a comprehensive quality report dictionary with status warnings.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image

    # 1. Blur detection via Laplacian Variance
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    if laplacian_var < 80:
        blur_status = "BLURRY"
        blur_warning = "Image is noticeably blurry; OCR accuracy may be reduced."
    elif laplacian_var < 200:
        blur_status = "MODERATE"
        blur_warning = None
    else:
        blur_status = "SHARP"
        blur_warning = None

    # 2. Brightness & Contrast
    mean_brightness = float(np.mean(gray))
    std_contrast = float(np.std(gray))

    # 3. Glare Detection Index (percentage of near-saturated pixels)
    glare_pixels = np.sum(gray >= 245)
    total_pixels = gray.size
    glare_ratio = float(glare_pixels / total_pixels) * 100.0

    lighting_warning = None
    if mean_brightness < 50:
        lighting_warning = "Image is very dark / underexposed."
    elif mean_brightness > 220 or glare_ratio > 15.0:
        lighting_warning = f"Image is washed out / glare detected ({round(glare_ratio, 1)}% saturated)."

    # 4. Resolution check
    h, w = gray.shape[:2]
    resolution_ok = (w >= 400 and h >= 300)

    quality_score = 100.0
    if blur_status == "BLURRY":
        quality_score -= 35.0
    elif blur_status == "MODERATE":
        quality_score -= 10.0

    if lighting_warning:
        quality_score -= 20.0
    if not resolution_ok:
        quality_score -= 25.0

    quality_score = max(10.0, min(100.0, quality_score))

    return {
        "quality_score": round(quality_score, 2),
        "blur_status": blur_status,
        "laplacian_variance": round(laplacian_var, 2),
        "brightness": round(mean_brightness, 2),
        "contrast": round(std_contrast, 2),
        "glare_percentage": round(glare_ratio, 2),
        "resolution": f"{w}x{h}",
        "is_acceptable": quality_score >= 50.0,
        "warnings": [w for w in [blur_warning, lighting_warning] if w is not None]
    }


def deskew_image(image, max_angle=30.0):
    """
    Detects skew angle of document text/contours and straightens the image.
    Limits rotation to max_angle to avoid unwanted 90-degree flips.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
    
    # Invert and threshold to get text/foreground mask
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    
    # Find all foreground coordinates
    coords = np.column_stack(np.where(thresh > 0))
    if len(coords) < 100:
        return image, 0.0

    # Calculate minimum bounding rectangle
    rect = cv2.minAreaRect(coords)
    angle = rect[-1]

    # Normalize angle
    if angle < -45:
        angle = -(90 + angle)
    elif angle > 45:
        angle = 90 - angle
    else:
        angle = -angle

    # Only correct if within plausible document skew range (e.g. +/- 30 degrees)
    if abs(angle) > max_angle or abs(angle) < 0.5:
        return image, 0.0

    # Rotate image around center
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    rot_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(
        image,
        rot_matrix,
        (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE
    )

    return rotated, round(angle, 2)


def preprocess_document_image(image_input, scale_factor=2.0):
    """
    Comprehensive document image preprocessor.
    Performs quality assessment, deskewing, scaling, CLAHE contrast enhancement,
    bilateral filtering, and multi-mode thresholding.
    
    Returns:
        dict containing:
            'original': loaded RGB image
            'gray_resized': 2x upscaled grayscale with noise filter
            'clahe_enhanced': CLAHE contrast enhanced image
            'otsu_thresh': Otsu binarized image
            'adaptive_thresh': Adaptive Gaussian binarized image
            'quality': quality report dictionary
            'skew_angle': detected rotation angle corrected
    """
    if isinstance(image_input, str):
        if not os.path.exists(image_input):
            raise FileNotFoundError(f"Image not found: {image_input}")
        image = cv2.imread(image_input)
        if image is None:
            raise ValueError(f"Could not read image: {image_input}")
    elif isinstance(image_input, np.ndarray):
        image = image_input.copy()
    else:
        raise TypeError("Invalid image input type")

    # 1. Image Quality Assessment
    quality_report = assess_image_quality(image)

    # 2. Deskewing
    deskewed_image, angle = deskew_image(image)

    # 3. Grayscale conversion
    gray = cv2.cvtColor(deskewed_image, cv2.COLOR_BGR2GRAY)

    # 4. Standardize resolution to optimal OCR dimensions (~1400px width)
    h, w = gray.shape[:2]
    target_width = 1400
    if w != target_width:
        scale_ratio = target_width / float(w)
        target_height = int(h * scale_ratio)
        gray_resized = cv2.resize(
            gray,
            (target_width, target_height),
            interpolation=cv2.INTER_CUBIC if scale_ratio > 1.0 else cv2.INTER_AREA
        )
    else:
        gray_resized = gray.copy()

    # 5. CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    clahe_enhanced = clahe.apply(gray_resized)

    # 6. Bilateral Filtering for edge-preserving smoothing
    bilateral = cv2.bilateralFilter(gray_resized, 9, 75, 75)

    # 7. Gaussian noise smoothing
    blurred = cv2.GaussianBlur(gray_resized, (3, 3), 0)

    # 8. Otsu thresholding
    otsu_thresh = cv2.threshold(
        blurred,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )[1]

    # 9. Adaptive thresholding
    adaptive_thresh = cv2.adaptiveThreshold(
        gray_resized,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        11
    )

    return {
        "original": deskewed_image,
        "gray_resized": gray_resized,
        "clahe_enhanced": clahe_enhanced,
        "bilateral": bilateral,
        "otsu_thresh": otsu_thresh,
        "adaptive_thresh": adaptive_thresh,
        "quality": quality_report,
        "skew_angle": angle
    }


# Backwards compatibility alias
def preprocess_image(image_path):
    res = preprocess_document_image(image_path)
    return res["gray_resized"]


if __name__ == "__main__":
    import sys
    test_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join("input", "passport.jpg")
    print(f"Testing Preprocessing on: {test_path}")
    data = preprocess_document_image(test_path)
    print("\nQuality Report:")
    for k, v in data["quality"].items():
        print(f"  {k:<20}: {v}")
    print(f"Skew Corrected: {data['skew_angle']}°")
    os.makedirs("output", exist_ok=True)
    cv2.imwrite("output/preprocessed.jpg", data["gray_resized"])
    print("Saved: output/preprocessed.jpg")