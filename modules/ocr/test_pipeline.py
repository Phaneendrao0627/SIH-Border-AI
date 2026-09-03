# ============================================================
# AI-BASED FAKE IDENTITY & DOCUMENT SCREENING SYSTEM
# MODULE 1: COMPREHENSIVE PIPELINE TEST SUITE
# ============================================================

import os
import sys
import unittest
import json

from image_preprocessing import preprocess_document_image, assess_image_quality
from document_classifier import classify_document
from face_detector import detect_and_crop_face
from processors.passport_processor import calculate_check_digit, check_digit_valid, process_passport
from processors import process_by_type
from app import process_document


class TestModule1Pipeline(unittest.TestCase):

    def setUp(self):
        self.input_dir = "input"
        self.output_dir = "output"
        os.makedirs(self.output_dir, exist_ok=True)

    def test_01_mrz_check_digit_algorithm(self):
        """Verify ICAO 9303 7-3-1 check digit computation."""
        # Test known check digit
        # Passport number "P3938806" -> check digit '4'
        cd = calculate_check_digit("P3938806")
        self.assertEqual(cd, 4)
        self.assertTrue(check_digit_valid("P3938806", "4"))
        self.assertFalse(check_digit_valid("P3938806", "5"))

        # Test date check digits
        # 820406 (6 April 1982) -> check digit '6'
        self.assertEqual(calculate_check_digit("820406"), 6)
        # 260828 (28 August 2026) -> check digit '2'
        self.assertEqual(calculate_check_digit("260828"), 2)

    def test_02_document_classifier(self):
        """Verify classifier detects all required document types."""
        self.assertEqual(classify_document("REPUBLIC OF INDIA PASSPORT P<IND"), "PASSPORT")
        self.assertEqual(classify_document("UNITED STATES VISA TYPE B1/B2"), "VISA")
        self.assertEqual(classify_document("GOVERNMENT OF INDIA AADHAAR CARD ENROLMENT"), "NATIONAL_ID")
        self.assertEqual(classify_document("UNION OF INDIA DRIVING LICENCE DL NO"), "DRIVING_LICENSE")
        self.assertEqual(classify_document("RESIDENCE PERMIT MINISTRY OF HOME AFFAIRS"), "PERMIT")

    def test_03_image_quality_assessment(self):
        """Verify sharpness, resolution, and quality scoring."""
        passport_path = os.path.join(self.input_dir, "passport.jpg")
        if os.path.exists(passport_path):
            prep = preprocess_document_image(passport_path)
            quality = prep["quality"]
            self.assertIn("quality_score", quality)
            self.assertIn("blur_status", quality)
            self.assertGreater(quality["quality_score"], 0)

    def test_04_face_detector(self):
        """Verify face detection and cropping for Module 4."""
        passport_path = os.path.join(self.input_dir, "passport.jpg")
        if os.path.exists(passport_path):
            face_result = detect_and_crop_face(passport_path, output_path=os.path.join(self.output_dir, "test_face.jpg"))
            self.assertTrue(face_result["face_detected"])
            self.assertGreater(face_result["confidence"], 70.0)
            self.assertTrue(os.path.exists(os.path.join(self.output_dir, "test_face.jpg")))

    def test_05_end_to_end_passport_pipeline(self):
        """Verify full process_document pipeline output on passport."""
        passport_path = os.path.join(self.input_dir, "passport.jpg")
        if os.path.exists(passport_path):
            result = process_document(passport_path, output_dir=self.output_dir)
            self.assertEqual(result["document_type"], "PASSPORT")
            self.assertEqual(result["status"], "VERIFIED")
            self.assertEqual(result["identity"]["surname"], "ATTHI")
            self.assertEqual(result["identity"]["given_name"], "MADHAVI")
            self.assertEqual(result["document"]["document_number"], "P3938806")
            self.assertTrue(result["face_extraction"]["face_detected"])
            self.assertTrue(result["verification"]["mrz_valid"])
            self.assertEqual(result["verification"]["confidence_level"], "HIGH")

            # Check final JSON file
            final_json = os.path.join(self.output_dir, "final_document.json")
            self.assertTrue(os.path.exists(final_json))
            with open(final_json, "r", encoding="utf-8") as f:
                saved_data = json.load(f)
                self.assertEqual(saved_data["document_type"], "PASSPORT")


if __name__ == "__main__":
    print("\n" + "=" * 65)
    print("   RUNNING MODULE 1 COMPREHENSIVE REGRESSION TEST SUITE")
    print("=" * 65 + "\n")
    unittest.main(verbosity=2)
