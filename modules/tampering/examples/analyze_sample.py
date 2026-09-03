"""Demonstration script showing library usage of Module 3: Tampering Detection."""

import json
import sys
from pathlib import Path

# Add project root to sys.path for standalone execution
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import cv2
import numpy as np

from tampering_detection.api import analyze_document
from tampering_detection.config import DetectionConfig


def create_synthetic_test_documents(output_dir: Path):
    """Generate realistic synthetic document images for demonstration purposes."""
    output_dir.mkdir(parents=True, exist_ok=True)
    width, height = 800, 600

    # 1. Base clean document (light grey background with fine printed noise)
    base = np.full((height, width, 3), 245, dtype=np.uint8)
    np.random.seed(42)
    noise = np.random.normal(0, 2, (height, width, 3)).astype(np.int16)
    clean_doc = np.clip(base.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    # Add header text
    cv2.putText(clean_doc, "REPUBLIC OF PASSPORTIA", (220, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (40, 40, 40), 2)
    cv2.putText(clean_doc, "OFFICIAL IDENTITY DOCUMENT", (260, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (90, 90, 90), 1)

    # Add photo region (x=100, y=120, w=260, h=320) with matching natural backdrop
    photo_area = np.full((320, 260, 3), 225, dtype=np.uint8)
    photo_noise = np.random.normal(0, 2, (320, 260, 3)).astype(np.int16)
    photo_area = np.clip(photo_area.astype(np.int16) + photo_noise, 0, 255).astype(np.uint8)
    cv2.circle(photo_area, (130, 120), 50, (140, 140, 140), -1)  # Synthetic head
    cv2.ellipse(photo_area, (130, 240), (80, 70), 0, 0, 180, (120, 120, 120), -1)  # Synthetic torso
    clean_doc[120:440, 100:360] = photo_area

    # Add text fields (date_of_birth, passport_number)
    cv2.putText(clean_doc, "DATE OF BIRTH:", (420, 210), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (80, 80, 80), 1)
    cv2.putText(clean_doc, "14 AUG 1985", (420, 245), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (30, 30, 30), 2)

    cv2.putText(clean_doc, "DOCUMENT NUMBER:", (420, 275), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (80, 80, 80), 1)
    cv2.putText(clean_doc, "A98765432", (420, 310), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (30, 30, 30), 2)

    # Add entry stamp (x=260, y=480, w=220, h=90)
    cv2.circle(clean_doc, (370, 525), 40, (0, 0, 160), 2)
    cv2.putText(clean_doc, "ARRIVED", (340, 530), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 160), 2)

    clean_path = output_dir / "clean_passport.jpg"
    cv2.imwrite(str(clean_path), clean_doc, [cv2.IMWRITE_JPEG_QUALITY, 90])

    # 2. Tampered Document (Photo replacement with high noise + Text patch + Cloned stamp)
    tampered_doc = clean_doc.copy()

    # Tamper 1: Spliced photo with mismatched high noise & boundary discontinuity
    tampered_photo = np.full((320, 260, 3), 80, dtype=np.uint8)
    high_noise = np.random.normal(0, 30, (320, 260, 3)).astype(np.int16)
    tampered_photo = np.clip(tampered_photo.astype(np.int16) + high_noise, 0, 255).astype(np.uint8)
    cv2.circle(tampered_photo, (130, 120), 48, (200, 160, 150), -1)
    tampered_doc[120:440, 100:360] = tampered_photo

    # Tamper 2: Text manipulation with white rectangular patch artifact
    cv2.rectangle(tampered_doc, (415, 210), (595, 255), (255, 255, 255), -1)  # Flat white erase box
    cv2.putText(tampered_doc, "22 DEC 1999", (420, 247), cv2.FONT_HERSHEY_SIMPLEX, 0.70, (0, 0, 0), 2)

    # Tamper 3: Cloned duplicate stamp pasted elsewhere on the page
    stamp_crop = tampered_doc[480:570, 260:480].copy()
    tampered_doc[480:570, 520:740] = stamp_crop

    tampered_path = output_dir / "tampered_passport.jpg"
    cv2.imwrite(str(tampered_path), tampered_doc, [cv2.IMWRITE_JPEG_QUALITY, 90])

    return clean_path, tampered_path


def main():
    print("=" * 70)
    print("MODULE 3: TAMPERING DETECTION — PASSPORT DEMONSTRATION")
    print("=" * 70)

    samples_dir = Path("samples")
    clean_path = samples_dir / "clean_passport.jpg"
    tampered_path = samples_dir / "tampered_passport.jpg"

    if not clean_path.exists() or not tampered_path.exists():
        clean_path, tampered_path = create_synthetic_test_documents(samples_dir)

    regions_file = Path("examples/sample_regions.json")
    if regions_file.exists():
        with open(regions_file, "r", encoding="utf-8") as f:
            regions = json.load(f)
    else:
        regions = None

    config = DetectionConfig(
        save_artifacts=True,
        artifacts_dir="results/demo_artifacts",
    )

    # 1. Analyze Clean Document
    print("\n[1] Running forensic analysis on CLEAN document...")
    result_clean = analyze_document(
        image_source=str(clean_path),
        document_id="DOC-CLEAN-001",
        document_type="passport",
        regions=regions,
        options=config,
    )
    print(f"-> Tampering Score: {result_clean.tampering_score}/100")
    print(f"-> Risk Level:      {result_clean.risk_level.value}")
    print(f"-> Confidence:      {result_clean.confidence}")
    print(f"-> Flags:           {result_clean.flags}")

    # 2. Analyze Tampered Document
    print("\n[2] Running forensic analysis on TAMPERED document...")
    result_tampered = analyze_document(
        image_source=str(tampered_path),
        document_id="DOC-FORGED-999",
        document_type="passport",
        regions=regions,
        options=config,
    )
    print(f"-> Tampering Score: {result_tampered.tampering_score}/100")
    print(f"-> Risk Level:      {result_tampered.risk_level.value}")
    print(f"-> Confidence:      {result_tampered.confidence}")
    print(f"-> Flags:           {result_tampered.flags}")
    print("\n-> Explainable Forensic Evidence:")
    for ev in result_tampered.evidence:
        print(f"   [{ev.severity.value.upper()}] {ev.detector} - {ev.signal}:")
        print(f"      {ev.description}")

    if result_tampered.artifacts.ela_map:
        print(f"\n-> Visual Heatmap generated: {result_tampered.artifacts.ela_map}")
    if result_tampered.artifacts.region_visualizations:
        print(f"-> Region Overlay generated: {result_tampered.artifacts.region_visualizations[0]}")

    print("\n" + "=" * 70)
    print("Demonstration completed successfully.")
    print("=" * 70)


if __name__ == "__main__":
    main()
