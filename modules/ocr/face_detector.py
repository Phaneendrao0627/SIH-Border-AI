# ============================================================
# AI-BASED FAKE IDENTITY & DOCUMENT SCREENING SYSTEM
# MODULE 1: FACE DETECTOR & PHOTO CROPPER (FOR MODULE 4)
# ============================================================

import os
import sys
import cv2
import numpy as np
import urllib.request

MODEL_FILENAME = "face_detection_yunet_2023mar.onnx"
MODEL_URL = "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx"
OUTPUT_DIR = "output"
DEFAULT_FACE_OUTPUT = os.path.join(OUTPUT_DIR, "face.jpg")


def get_model_path():
    """
    Ensure YuNet ONNX model is available locally.
    Downloads it automatically if not present (~230 KB).
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(current_dir, MODEL_FILENAME)

    if not os.path.exists(model_path):
        print(f"📥 Downloading face detection model ({MODEL_FILENAME})...")
        try:
            urllib.request.urlretrieve(MODEL_URL, model_path)
            print("✅ Model downloaded successfully.")
        except Exception as e:
            print(f"⚠️ Could not download model: {e}")
            return None

    return model_path


def detect_and_crop_face(
    image_input,
    output_path=DEFAULT_FACE_OUTPUT,
    score_threshold=0.6,
    padding_ratio=0.25
):
    """
    Detects the primary face / portrait photo in an identity document,
    crops it with clean padding, and saves it for Module 4 (Face Verification).

    Parameters:
        image_input: File path (str) or loaded cv2 numpy image array
        output_path: Where to save cropped face (default: output/face.jpg)
        score_threshold: Minimum confidence score (0.0 to 1.0)
        padding_ratio: Margin to add around face bounding box (e.g. 0.25 for 25%)

    Returns:
        dict: {
            "face_detected": bool,
            "face_image_path": str or None,
            "confidence": float,
            "bounding_box": [x, y, w, h] or None,
            "cropped_dimensions": (height, width) or None
        }
    """
    # 1. Load image
    if isinstance(image_input, str):
        if not os.path.exists(image_input):
            return {
                "face_detected": False,
                "face_image_path": None,
                "confidence": 0.0,
                "bounding_box": None,
                "error": f"Image file not found: {image_input}"
            }
        image = cv2.imread(image_input)
        if image is None:
            return {
                "face_detected": False,
                "face_image_path": None,
                "confidence": 0.0,
                "bounding_box": None,
                "error": f"Could not decode image: {image_input}"
            }
    elif isinstance(image_input, np.ndarray):
        image = image_input.copy()
    else:
        return {
            "face_detected": False,
            "face_image_path": None,
            "confidence": 0.0,
            "bounding_box": None,
            "error": "Invalid image input type"
        }

    img_h, img_w = image.shape[:2]

    # 2. Get face detector model
    model_path = get_model_path()
    faces = None

    if model_path and os.path.exists(model_path) and hasattr(cv2, "FaceDetectorYN_create"):
        try:
            detector = cv2.FaceDetectorYN_create(
                model_path,
                "",
                (img_w, img_h),
                score_threshold=score_threshold,
                nms_threshold=0.3,
                top_k=5
            )
            detector.setInputSize((img_w, img_h))
            _, faces = detector.detect(image)
        except Exception as e:
            print(f"⚠️ FaceDetectorYN failed: {e}")

    # 3. Fallback to Haar cascade if available
    if faces is None or len(faces) == 0:
        if hasattr(cv2, "CascadeClassifier") and hasattr(cv2, "data") and hasattr(cv2.data, "haarcascades"):
            cascade_path = os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml")
            if os.path.exists(cascade_path):
                cascade = cv2.CascadeClassifier(cascade_path)
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                haar_faces = cascade.detectMultiScale(
                    gray,
                    scaleFactor=1.1,
                    minNeighbors=4,
                    minSize=(40, 40)
                )
                if len(haar_faces) > 0:
                    faces = []
                    for (hx, hy, hw, hh) in haar_faces:
                        faces.append([hx, hy, hw, hh, 0.85])
                    faces = np.array(faces)

    # 4. Process detection results
    if faces is None or len(faces) == 0:
        return {
            "face_detected": False,
            "face_image_path": None,
            "confidence": 0.0,
            "bounding_box": None,
            "message": "No face detected in document"
        }

    # Select the most prominent face (largest area with good confidence)
    best_face = None
    max_area = 0
    best_conf = 0.0

    for face in faces:
        x, y, w, h = int(face[0]), int(face[1]), int(face[2]), int(face[3])
        conf = float(face[-1]) if len(face) > 4 else 0.85
        area = w * h
        if area > max_area and conf >= score_threshold:
            max_area = area
            best_face = (x, y, w, h)
            best_conf = conf

    if best_face is None:
        return {
            "face_detected": False,
            "face_image_path": None,
            "confidence": 0.0,
            "bounding_box": None,
            "message": "Face candidates below confidence threshold"
        }

    x, y, w, h = best_face

    # 5. Apply padding around the face for clean portrait crop
    pad_w = int(w * padding_ratio)
    pad_h = int(h * padding_ratio)

    x1 = max(0, x - pad_w)
    y1 = max(0, y - pad_h)
    x2 = min(img_w, x + w + pad_w)
    y2 = min(img_h, y + h + pad_h)

    face_crop = image[y1:y2, x1:x2]

    if face_crop.size == 0:
        return {
            "face_detected": False,
            "face_image_path": None,
            "confidence": 0.0,
            "bounding_box": None,
            "error": "Face cropping failed"
        }

    # 6. Save cropped face image
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    cv2.imwrite(output_path, face_crop)

    return {
        "face_detected": True,
        "face_image_path": output_path,
        "confidence": round(best_conf * 100, 2),
        "bounding_box": [int(x1), int(y1), int(x2 - x1), int(y2 - y1)],
        "cropped_dimensions": (int(face_crop.shape[0]), int(face_crop.shape[1]))
    }


if __name__ == "__main__":
    test_image = sys.argv[1] if len(sys.argv) > 1 else os.path.join("input", "passport.jpg")

    print("\n" + "=" * 60)
    print("      AI-BASED DOCUMENT SCREENING - FACE DETECTOR")
    print("=" * 60)
    print(f"Input Document : {test_image}")

    result = detect_and_crop_face(test_image)

    print("\n========== FACE DETECTION RESULT ==========")
    for k, v in result.items():
        print(f"{k:<20}: {v}")
    print("===========================================\n")
