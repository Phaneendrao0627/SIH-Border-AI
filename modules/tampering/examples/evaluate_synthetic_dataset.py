"""Evaluation benchmark script on synthetic document dataset.

Calculates:
- True Positives (TP)
- True Negatives (TN)
- False Positives (FP)
- False Negatives (FN)
- Precision, Recall, F1 Score
- Confusion Matrix

NOTE: Results generated from synthetic tests are strictly for demo, development,
and heuristic verification. They do NOT represent real-world forensic accuracy on
physical border documents or high-end professional forgeries.
"""

import io
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Add project root to sys.path for standalone execution
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import cv2
import numpy as np
from PIL import Image

from tampering_detection.api import analyze_document
from tampering_detection.config import DetectionConfig
from tampering_detection.schemas import RiskLevel


def generate_synthetic_dataset(num_samples: int = 20) -> List[Tuple[np.ndarray, bool, Dict]]:
    """Generate a balanced synthetic batch of clean and tampered document images.

    Returns:
        List of tuples: (image_bgr_array, is_tampered_ground_truth, regions_dict)
    """
    dataset = []
    w, h = 640, 480

    for i in range(num_samples):
        is_tampered = (i % 2 == 1)
        np.random.seed(1000 + i)

        # Baseline document
        doc = np.full((h, w, 3), 240, dtype=np.uint8)
        noise = np.random.normal(0, 2, (h, w, 3)).astype(np.int16)
        doc = np.clip(doc.astype(np.int16) + noise, 0, 255).astype(np.uint8)

        # Printed borders and header
        cv2.putText(doc, f"STATE PERMIT #{10000 + i}", (150, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (50, 50, 50), 2)

        # Photo region (x=60, y=80, w=180, h=220) with matching natural backdrop
        px, py, pw, ph = 60, 80, 180, 220
        photo = np.full((ph, pw, 3), 230, dtype=np.uint8)
        p_noise = np.random.normal(0, 2, (ph, pw, 3)).astype(np.int16)
        photo = np.clip(photo.astype(np.int16) + p_noise, 0, 255).astype(np.uint8)
        cv2.circle(photo, (pw // 2, 90), 40, (130, 130, 130), -1)
        cv2.rectangle(photo, (pw // 2 - 50, 150), (pw // 2 + 50, 220), (100, 100, 100), -1)
        doc[py : py + ph, px : px + pw] = photo

        # Text regions
        tx1, ty1, tw1, th1 = 280, 120, 200, 35
        cv2.putText(doc, "NAME: CITIZEN TEST", (tx1 + 5, ty1 + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (40, 40, 40), 1)

        tx2, ty2, tw2, th2 = 280, 180, 200, 35
        cv2.putText(doc, "EXPIRY: 2030-01-01", (tx2 + 5, ty2 + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (40, 40, 40), 1)

        # Stamp region (circular authentic seal)
        sx, sy, sw, sh = 200, 330, 200, 100
        cv2.circle(doc, (sx + sw // 2, sy + sh // 2), 35, (0, 0, 150), 2)
        cv2.putText(doc, "VERIFIED", (sx + 45, sy + 55), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 150), 2)

        regions = {
            "photo": [{"name": "photo_id", "x": px, "y": py, "width": pw, "height": ph}],
            "text": [
                {"name": "field_name", "x": tx1, "y": ty1, "width": tw1, "height": th1},
                {"name": "field_expiry", "x": tx2, "y": ty2, "width": tw2, "height": th2},
            ],
            "stamp": [{"name": "customs_stamp", "x": sx, "y": sy, "width": sw, "height": sh}],
        }

        # Apply tamper manipulations if ground truth is tampered
        if is_tampered:
            manipulation_type = (i // 2) % 3
            if manipulation_type == 0:
                # Tamper Photo: Noise mismatch + dark spliced portrait
                spliced_photo = np.full((ph, pw, 3), 70, dtype=np.uint8)
                s_noise = np.random.normal(0, 30, (ph, pw, 3)).astype(np.int16)
                spliced_photo = np.clip(spliced_photo.astype(np.int16) + s_noise, 0, 255).astype(np.uint8)
                cv2.circle(spliced_photo, (pw // 2, 90), 38, (190, 150, 140), -1)
                doc[py : py + ph, px : px + pw] = spliced_photo

            elif manipulation_type == 1:
                # Tamper Text: Erase date and paste darker mismatched font
                cv2.rectangle(doc, (tx2, ty2), (tx2 + tw2, ty2 + th2), (255, 255, 255), -1)
                cv2.putText(doc, "EXPIRY: 2099-12-31", (tx2 + 5, ty2 + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.70, (0, 0, 0), 3)

            else:
                # Tamper Stamp: Flat white background cutout + duplicate stamp
                dup_crop = doc[sy : sy + sh, sx : sx + sw].copy()
                doc[sy : sy + sh, sx + 220 : sx + 220 + sw] = dup_crop
                regions["stamp"].append(
                    {"name": "customs_stamp_dup", "x": sx + 220, "y": sy, "width": sw, "height": sh}
                )

        dataset.append((doc, is_tampered, regions))

    return dataset


def evaluate():
    print("=" * 70)
    print("SYNTHETIC BENCHMARK EVALUATION — MODULE 3 TAMPERING DETECTION")
    print("=" * 70)
    print("Generating 20 balanced synthetic test documents (10 Authentic, 10 Tampered)...")

    dataset = generate_synthetic_dataset(num_samples=20)
    config = DetectionConfig(privacy_mode=True)

    tp, fp, tn, fn = 0, 0, 0, 0

    for idx, (img_bgr, is_tampered, regions) in enumerate(dataset):
        res = analyze_document(
            image_source=img_bgr,
            document_id=f"EVAL-{idx:03d}",
            regions=regions,
            options=config,
        )

        # Classification criterion: Tampering suspected if score >= 45 or risk level is HIGH/CRITICAL
        # or specific tampering flag raised
        predicted_tampered = (
            res.tampering_score >= 45
            or res.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)
            or "photo_replacement_suspected" in res.flags
            or "stamp_forgery_suspected" in res.flags
            or "text_manipulation_suspected" in res.flags
        )

        if is_tampered and predicted_tampered:
            tp += 1
        elif not is_tampered and not predicted_tampered:
            tn += 1
        elif not is_tampered and predicted_tampered:
            fp += 1
        elif is_tampered and not predicted_tampered:
            fn += 1

    precision = tp / float(tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / float(tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    accuracy = (tp + tn) / float(tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0.0

    print("\n" + "-" * 50)
    print("BENCHMARK METRICS SUMMARY:")
    print("-" * 50)
    print(f"Total Evaluated:         {len(dataset)}")
    print(f"True Positives (TP):     {tp}")
    print(f"True Negatives (TN):     {tn}")
    print(f"False Positives (FP):    {fp}")
    print(f"False Negatives (FN):    {fn}")
    print(f"Accuracy:                {accuracy * 100:.1f}%")
    print(f"Precision:               {precision:.3f}")
    print(f"Recall:                  {recall:.3f}")
    print(f"F1 Score:                {f1:.3f}")
    print("-" * 50)
    print("\nCONFUSION MATRIX:")
    print("                    Predicted Genuine     Predicted Tampered")
    print(f"Actual Genuine:          {tn:<20}  {fp:<20}")
    print(f"Actual Tampered:         {fn:<20}  {tp:<20}")
    print("\n" + "=" * 70)
    print("DISCLAIMER: These synthetic benchmark results validate the heuristic")
    print("pipeline implementation and do not guarantee real-world border forensic rates.")
    print("=" * 70)


if __name__ == "__main__":
    evaluate()
