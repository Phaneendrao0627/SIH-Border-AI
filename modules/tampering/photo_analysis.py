from PIL import Image, ImageChops, ImageEnhance
import cv2
import os


def detect_face_region(image_path):
    """
    Automatically detects the largest face in the document.

    This removes the dependency on a fixed passport photo box.
    Works with different document sizes and layouts.
    """

    image = cv2.imread(image_path)

    if image is None:
        raise FileNotFoundError(
            f"Unable to read image: {image_path}"
        )

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    cascade_path = cv2.data.haarcascades + (
        "haarcascade_frontalface_default.xml"
    )

    detector = cv2.CascadeClassifier(
        cascade_path
    )

    faces = detector.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(30, 30)
    )

    if len(faces) == 0:
        return None

    # Select largest detected face
    largest = max(
        faces,
        key=lambda box: box[2] * box[3]
    )

    x, y, w, h = largest

    image_height, image_width = gray.shape

    # Expand around face to cover the photograph region
    padding_x = int(w * 0.9)
    padding_top = int(h * 0.8)
    padding_bottom = int(h * 1.4)

    x1 = max(0, x - padding_x)
    y1 = max(0, y - padding_top)

    x2 = min(
        image_width,
        x + w + padding_x
    )

    y2 = min(
        image_height,
        y + h + padding_bottom
    )

    return (
        x1,
        y1,
        x2,
        y2
    )


def analyze_photo(image_path, output_prefix):
    """
    Adaptive document photo analysis.

    Uses automatic face detection instead of a fixed
    passport-specific coordinate box.
    """

    if not os.path.exists(image_path):
        raise FileNotFoundError(
            f"Image not found: {image_path}"
        )

    original = Image.open(
        image_path
    ).convert("RGB")

    width, height = original.size

    # --------------------------------------------------------
    # FACE DETECTION
    # --------------------------------------------------------

    photo_box = detect_face_region(
        image_path
    )

    # --------------------------------------------------------
    # OUTPUT DIRECTORY
    # --------------------------------------------------------

    output_dir = os.path.dirname(
        output_prefix
    )

    if output_dir:
        os.makedirs(
            output_dir,
            exist_ok=True
        )

    # --------------------------------------------------------
    # CASE 1:
    # FACE FOUND
    # --------------------------------------------------------

    if photo_box is not None:

        x1, y1, x2, y2 = photo_box

        # ----------------------------------------------------
        # JPEG RECOMPRESSION
        # ----------------------------------------------------

        temp_path = (
            "temp_photo_reference.jpg"
        )

        original.save(
            temp_path,
            "JPEG",
            quality=90
        )

        recompressed = Image.open(
            temp_path
        ).convert("RGB")

        # ----------------------------------------------------
        # ELA
        # ----------------------------------------------------

        difference = ImageChops.difference(
            original,
            recompressed
        )

        ela = ImageEnhance.Brightness(
            difference
        ).enhance(10)

        # ----------------------------------------------------
        # CROP PHOTO REGION
        # ----------------------------------------------------

        photo = original.crop(
            photo_box
        )

        photo_ela = ela.crop(
            photo_box
        )

        grayscale = photo_ela.convert(
            "L"
        )

        pixels = list(
            grayscale.getdata()
        )

        average = (
            sum(pixels) /
            len(pixels)
        )

        maximum = max(pixels)

        high_pixels = sum(
            1
            for pixel in pixels
            if pixel > 30
        )

        percentage = (
            high_pixels /
            len(pixels)
        ) * 100

        # ----------------------------------------------------
        # PHOTO RISK
        # ----------------------------------------------------

        if percentage > 0.15:

            photo_score = 100

            result = (
                "HIGH PHOTO INCONSISTENCY"
            )

        elif percentage > 0.05:

            photo_score = 60

            result = (
                "MEDIUM PHOTO INCONSISTENCY"
            )

        else:

            photo_score = 10

            result = (
                "LOW PHOTO INCONSISTENCY"
            )

        # ----------------------------------------------------
        # SAVE
        # ----------------------------------------------------

        photo_output = (
            output_prefix +
            "_photo.jpg"
        )

        ela_output = (
            output_prefix +
            "_photo_ela.jpg"
        )

        photo.save(
            photo_output
        )

        photo_ela.save(
            ela_output
        )

        if os.path.exists(temp_path):
            os.remove(temp_path)

        return {

            "percentage": round(
                percentage,
                4
            ),

            "average": round(
                average,
                4
            ),

            "maximum": maximum,

            "high_pixels": high_pixels,

            "photo_score": photo_score,

            "result": result,

            "photo_detected": True,

            "photo_box": photo_box,

            "photo_output": photo_output,

            "ela_output": ela_output
        }

    # --------------------------------------------------------
    # CASE 2:
    # NO FACE FOUND
    # --------------------------------------------------------

    else:

        # No face is important evidence, but we don't
        # automatically declare the whole document fake.

        photo_score = 80

        result = (
            "PHOTO/FACE NOT DETECTED - "
            "REQUIRES REVIEW"
        )

        photo_output = (
            output_prefix +
            "_photo.jpg"
        )

        ela_output = (
            output_prefix +
            "_photo_ela.jpg"
        )

        # Save complete image as reference
        original.save(
            photo_output
        )

        original.save(
            ela_output
        )

        return {

            "percentage": 0.0,

            "average": 0.0,

            "maximum": 0,

            "high_pixels": 0,

            "photo_score": photo_score,

            "result": result,

            "photo_detected": False,

            "photo_box": None,

            "photo_output": photo_output,

            "ela_output": ela_output
        }


# ============================================================
# STANDALONE TEST
# ============================================================

if __name__ == "__main__":

    genuine = (
        "test_documents/genuine/"
        "genuine2.jpeg"
    )

    tampered = (
        "test_documents/tampered/"
        "tampered2.jpg"
    )

    os.makedirs(
        "outputs/photo_analysis",
        exist_ok=True
    )

    print()
    print("========================================")
    print("       ADAPTIVE PHOTO ANALYSIS")
    print("========================================")

    print()
    print("GENUINE")

    result = analyze_photo(
        genuine,
        "outputs/photo_analysis/genuine"
    )

    print(
        "Face detected:",
        result["photo_detected"]
    )

    print(
        "Photo box:",
        result["photo_box"]
    )

    print(
        "Photo inconsistency:",
        result["percentage"],
        "%"
    )

    print(
        "Photo risk:",
        result["photo_score"],
        "/100"
    )

    print(
        "Result:",
        result["result"]
    )

    print()
    print("TAMPERED")

    result = analyze_photo(
        tampered,
        "outputs/photo_analysis/tampered"
    )

    print(
        "Face detected:",
        result["photo_detected"]
    )

    print(
        "Photo box:",
        result["photo_box"]
    )

    print(
        "Photo inconsistency:",
        result["percentage"],
        "%"
    )

    print(
        "Photo risk:",
        result["photo_score"],
        "/100"
    )

    print(
        "Result:",
        result["result"]
    )

    print("========================================")