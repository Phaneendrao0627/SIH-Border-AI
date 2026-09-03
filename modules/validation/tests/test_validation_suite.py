"""
Comprehensive Automated Test Suite for Module 2: Document Validation.
Covers all 30 test scenarios required by the system specification.
"""
from datetime import date
import os
import tempfile
import unittest

from document_validation.config import ValidationConfig
from document_validation.database.repository import BorderSecurityRepository
from document_validation.database.seeder import seed_mock_database
from document_validation.engine import DocumentValidationEngine
from document_validation.models.flags import ValidationFlag
from document_validation.models.result_model import ValidationStatus
from document_validation.validators.mrz_validator import calculate_icao_check_digit


class TestDocumentValidationSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_dir = tempfile.TemporaryDirectory()
        cls.db_path = os.path.join(cls.test_dir.name, "test_border.db")
        seed_mock_database(cls.db_path)
        cls.ref_date = date(2026, 9, 3)

        cls.config = ValidationConfig(
            db_path=cls.db_path,
            validation_date=cls.ref_date,
            expiring_soon_threshold_days=180,
            enable_database_checks=True
        )
        cls.engine = DocumentValidationEngine(config=cls.config)

    @classmethod
    def tearDownClass(cls):
        try:
            cls.test_dir.cleanup()
        except Exception:
            pass

    # 1. Fully valid passport
    def test_01_fully_valid_passport(self):
        payload = {
            "document_type": "passport",
            "nationality": "IND",
            "name": "RAHUL SHARMA",
            "passport_number": "M8392104",
            "date_of_birth": "1995-04-12",
            "date_of_expiry": "2032-08-20",
            "mrz_line_1": "P<INDSHARMA<<RAHUL<<<<<<<<<<<<<<<<<<<<<<<<<<",
            "mrz_line_2": "M8392104<3IND9504121M3208209<<<<<<<<<<<<<<<4",
            "mrz_checksum_score": 0.95,
            "ocr_confidence": 0.98
        }
        report = self.engine.validate(payload, validation_date=self.ref_date)
        self.assertEqual(report.overall_status, ValidationStatus.PASS)
        self.assertTrue(report.validation_results["format_valid"])
        self.assertTrue(report.validation_results["date_logic_valid"])
        self.assertTrue(report.validation_results["not_expired"])
        self.assertTrue(report.validation_results["mrz_checksum_valid"])
        self.assertFalse(report.validation_results["on_blacklist"])
        self.assertIn(ValidationFlag.STANDARDS_COMPLIANT.value, report.flags)

    # 2. Fully valid visa
    def test_02_fully_valid_visa(self):
        payload = {
            "document_type": "visa",
            "country_code": "USA",
            "name": "JOHN SMITH",
            "visa_number": "V1092837",
            "date_of_birth": "1988-06-15",
            "date_of_issue": "2026-01-10",
            "date_of_expiry": "2028-01-10",
            "visa_type": "B1/B2",
            "stay_duration": "90 days"
        }
        report = self.engine.validate(payload, validation_date=self.ref_date)
        self.assertEqual(report.overall_status, ValidationStatus.PASS)
        self.assertTrue(report.validation_results["date_logic_valid"])
        self.assertTrue(report.validation_results["not_expired"])

    # 3. Fully valid national ID
    def test_03_fully_valid_national_id(self):
        payload = {
            "document_type": "national_id",
            "country_code": "USA",
            "name": "ALICE WONDERLAND",
            "national_id_number": "ID9988221",
            "date_of_birth": "1992-10-05"
        }
        report = self.engine.validate(payload, validation_date=self.ref_date)
        self.assertEqual(report.overall_status, ValidationStatus.PASS)
        self.assertTrue(report.validation_results["format_valid"])

    # 4. Fully valid driving licence
    def test_04_fully_valid_driving_licence(self):
        payload = {
            "document_type": "driving_licence",
            "country_code": "IND",
            "name": "SANJAY MEHRA",
            "document_number": "DL99883344",
            "date_of_birth": "1985-03-20",
            "date_of_issue": "2020-03-20",
            "date_of_expiry": "2035-03-20"
        }
        report = self.engine.validate(payload, validation_date=self.ref_date)
        self.assertEqual(report.overall_status, ValidationStatus.PASS)

    # 5. Expired document
    def test_05_expired_document(self):
        payload = {
            "document_type": "passport",
            "nationality": "IND",
            "name": "RAHUL SHARMA",
            "passport_number": "M8392104",
            "date_of_birth": "1995-04-12",
            "date_of_expiry": "2024-05-01"  # Expired relative to 2026-09-03
        }
        report = self.engine.validate(payload, validation_date=self.ref_date)
        self.assertEqual(report.overall_status, ValidationStatus.FAIL)
        self.assertIn(ValidationFlag.EXPIRED_DOCUMENT.value, report.flags)
        self.assertFalse(report.validation_results["not_expired"])

    # 6. Future date of birth
    def test_06_future_date_of_birth(self):
        payload = {
            "document_type": "passport",
            "nationality": "IND",
            "name": "TEST BABY",
            "passport_number": "M8392104",
            "date_of_birth": "2028-01-01",  # Future relative to 2026-09-03
            "date_of_expiry": "2035-01-01"
        }
        report = self.engine.validate(payload, validation_date=self.ref_date)
        self.assertEqual(report.overall_status, ValidationStatus.FAIL)
        self.assertIn(ValidationFlag.FUTURE_DATE_OF_BIRTH.value, report.flags)
        self.assertFalse(report.validation_results["date_logic_valid"])

    # 7. Unrealistic date of birth (150 years old)
    def test_07_unrealistic_date_of_birth(self):
        payload = {
            "document_type": "passport",
            "nationality": "IND",
            "name": "ANCIENT TRAVELER",
            "passport_number": "M8392104",
            "date_of_birth": "1850-01-01",  # 176 years old
            "date_of_expiry": "2030-01-01"
        }
        report = self.engine.validate(payload, validation_date=self.ref_date)
        self.assertEqual(report.overall_status, ValidationStatus.FAIL)
        self.assertIn(ValidationFlag.UNREALISTIC_AGE.value, report.flags)

    # 8. Issue date after expiry date
    def test_08_issue_date_after_expiry_date(self):
        payload = {
            "document_type": "passport",
            "nationality": "IND",
            "name": "JOHN DOE",
            "passport_number": "M8392104",
            "date_of_birth": "1990-01-01",
            "date_of_issue": "2030-01-01",
            "date_of_expiry": "2025-01-01"  # Expiry before issue
        }
        report = self.engine.validate(payload, validation_date=self.ref_date)
        self.assertEqual(report.overall_status, ValidationStatus.FAIL)
        self.assertIn(ValidationFlag.EXPIRY_BEFORE_ISSUE.value, report.flags)

    # 9. Future issue date
    def test_09_future_issue_date(self):
        payload = {
            "document_type": "passport",
            "nationality": "IND",
            "name": "JOHN DOE",
            "passport_number": "M8392104",
            "date_of_birth": "1990-01-01",
            "date_of_issue": "2028-05-15",  # Future relative to 2026-09-03
            "date_of_expiry": "2038-05-15"
        }
        report = self.engine.validate(payload, validation_date=self.ref_date)
        self.assertEqual(report.overall_status, ValidationStatus.FAIL)
        self.assertIn(ValidationFlag.FUTURE_ISSUE_DATE.value, report.flags)

    # 10. Invalid document-number pattern
    def test_10_invalid_document_number_pattern(self):
        # Indian passport requires 1 letter + 7 digits: '12345678' is invalid
        payload = {
            "document_type": "passport",
            "nationality": "IND",
            "name": "JOHN DOE",
            "passport_number": "12345678",
            "date_of_birth": "1990-01-01",
            "date_of_expiry": "2030-01-01"
        }
        report = self.engine.validate(payload, validation_date=self.ref_date)
        self.assertEqual(report.overall_status, ValidationStatus.FAIL)
        self.assertIn(ValidationFlag.INVALID_DOCUMENT_NUMBER_FORMAT.value, report.flags)
        self.assertIn(ValidationFlag.COUNTRY_FORMAT_MISMATCH.value, report.flags)

    # 11. Invalid document-number length
    def test_11_invalid_document_number_length(self):
        # Length 7 instead of 8
        payload = {
            "document_type": "passport",
            "nationality": "IND",
            "name": "JOHN DOE",
            "passport_number": "M123456",
            "date_of_birth": "1990-01-01",
            "date_of_expiry": "2030-01-01"
        }
        report = self.engine.validate(payload, validation_date=self.ref_date)
        self.assertEqual(report.overall_status, ValidationStatus.FAIL)
        self.assertIn(ValidationFlag.INVALID_DOCUMENT_NUMBER_LENGTH.value, report.flags)

    # 12. Invalid characters in document number
    def test_12_invalid_characters(self):
        payload = {
            "document_type": "passport",
            "nationality": "IND",
            "name": "JOHN DOE",
            "passport_number": "M123#456",
            "date_of_birth": "1990-01-01",
            "date_of_expiry": "2030-01-01"
        }
        report = self.engine.validate(payload, validation_date=self.ref_date)
        self.assertEqual(report.overall_status, ValidationStatus.FAIL)
        self.assertIn(ValidationFlag.INVALID_DOCUMENT_NUMBER_CHARACTERS.value, report.flags)

    # 13. Missing required fields
    def test_13_missing_required_fields(self):
        payload = {
            "document_type": "passport",
            "nationality": "IND"
            # Missing document_number, name, date_of_birth
        }
        report = self.engine.validate(payload, validation_date=self.ref_date)
        self.assertEqual(report.overall_status, ValidationStatus.INCOMPLETE)
        self.assertIn(ValidationFlag.MISSING_DOCUMENT_NUMBER.value, report.flags)
        self.assertIn(ValidationFlag.MISSING_NAME.value, report.flags)

    # 14. Null and empty values
    def test_14_null_and_empty_values(self):
        payload = {
            "document_type": "passport",
            "nationality": "IND",
            "name": "",
            "document_number": None,
            "date_of_birth": "   "
        }
        report = self.engine.validate(payload, validation_date=self.ref_date)
        self.assertEqual(report.overall_status, ValidationStatus.INCOMPLETE)
        self.assertIn(ValidationFlag.MISSING_DOCUMENT_NUMBER.value, report.flags)
        self.assertIn(ValidationFlag.MISSING_NAME.value, report.flags)

    # 15. Invalid date formats
    def test_15_invalid_date_formats(self):
        # Non-leap year Feb 29
        payload = {
            "document_type": "passport",
            "nationality": "IND",
            "name": "LEAP YEAR FAIL",
            "passport_number": "M8392104",
            "date_of_birth": "2023-02-29",  # 2023 is not a leap year!
            "date_of_expiry": "2030-01-01"
        }
        report = self.engine.validate(payload, validation_date=self.ref_date)
        self.assertEqual(report.overall_status, ValidationStatus.FAIL)
        self.assertIn(ValidationFlag.INVALID_DATE_FORMAT.value, report.flags)

    # 16. Invalid MRZ line length
    def test_16_invalid_mrz_line_length(self):
        payload = {
            "document_type": "passport",
            "nationality": "IND",
            "name": "RAHUL SHARMA",
            "passport_number": "M8392104",
            "date_of_birth": "1995-04-12",
            "date_of_expiry": "2032-08-20",
            "mrz_line_1": "P<INDSHARMA<<RAHUL<<<<<<<<<<<<<<<<<<<<<<<<<<",
            "mrz_line_2": "M8392104<3IND9504121M3208209<<<<<"  # Too short (34 chars)
        }
        report = self.engine.validate(payload, validation_date=self.ref_date)
        self.assertEqual(report.overall_status, ValidationStatus.FAIL)
        self.assertIn(ValidationFlag.MRZ_STRUCTURE_INVALID.value, report.flags)

    # 17. Invalid MRZ checksum
    def test_17_invalid_mrz_checksum(self):
        # In line 2, change DOB check digit from '1' to '9'
        payload = {
            "document_type": "passport",
            "nationality": "IND",
            "name": "RAHUL SHARMA",
            "passport_number": "M8392104",
            "date_of_birth": "1995-04-12",
            "date_of_expiry": "2032-08-20",
            "mrz_line_1": "P<INDSHARMA<<RAHUL<<<<<<<<<<<<<<<<<<<<<<<<<<",
            "mrz_line_2": "M8392104<3IND9504129M3208209<<<<<<<<<<<<<<<4"  # Tampered DOB check digit
        }
        report = self.engine.validate(payload, validation_date=self.ref_date)
        self.assertEqual(report.overall_status, ValidationStatus.FAIL)
        self.assertIn(ValidationFlag.MRZ_CHECKSUM_INVALID.value, report.flags)

    # 18. MRZ / OCR field mismatch
    def test_18_mrz_ocr_field_mismatch(self):
        # OCR doc number is M8392104, but MRZ has Z7766554
        payload = {
            "document_type": "passport",
            "nationality": "IND",
            "name": "RAHUL SHARMA",
            "passport_number": "M8392104",
            "date_of_birth": "1995-04-12",
            "date_of_expiry": "2032-08-20",
            "mrz_line_1": "P<INDSHARMA<<RAHUL<<<<<<<<<<<<<<<<<<<<<<<<<<",
            "mrz_line_2": "Z7766554<3IND9504121M3208209<<<<<<<<<<<<<<<4"
        }
        report = self.engine.validate(payload, validation_date=self.ref_date)
        self.assertEqual(report.overall_status, ValidationStatus.FAIL)
        self.assertIn(ValidationFlag.MRZ_DOCUMENT_NUMBER_MISMATCH.value, report.flags)

    # 19. Valid MRZ with low OCR confidence
    def test_19_valid_mrz_with_low_ocr_confidence(self):
        payload = {
            "document_type": "passport",
            "nationality": "IND",
            "name": "RAHUL SHARMA",
            "passport_number": "M8392104",
            "date_of_birth": "1995-04-12",
            "date_of_expiry": "2032-08-20",
            "mrz_line_1": "P<INDSHARMA<<RAHUL<<<<<<<<<<<<<<<<<<<<<<<<<<",
            "mrz_line_2": "M8392104<3IND9504121M3208209<<<<<<<<<<<<<<<4",
            "mrz_checksum_score": 0.65,  # Low MRZ confidence (< 0.80)
            "ocr_confidence": 0.55       # Low OCR confidence (< 0.70)
        }
        report = self.engine.validate(payload, validation_date=self.ref_date)
        self.assertEqual(report.overall_status, ValidationStatus.WARN)
        self.assertIn(ValidationFlag.LOW_MRZ_CONFIDENCE.value, report.flags)
        self.assertIn(ValidationFlag.LOW_OCR_CONFIDENCE.value, report.flags)

    # 20. Blacklisted document number
    def test_20_blacklisted_document_number(self):
        # 'X9988776' is seeded in mock blacklist
        payload = {
            "document_type": "passport",
            "nationality": "IND",
            "name": "ARAVIND SWAMY",
            "passport_number": "X9988776",
            "date_of_birth": "1991-03-10",
            "date_of_expiry": "2030-05-10"
        }
        report = self.engine.validate(payload, validation_date=self.ref_date)
        self.assertEqual(report.overall_status, ValidationStatus.FAIL)
        self.assertTrue(report.validation_results["on_blacklist"])
        self.assertIn(ValidationFlag.DOCUMENT_ON_BLACKLIST.value, report.flags)
        self.assertIn(ValidationFlag.BLACKLIST_MATCH.value, report.flags)

    # 21. Watchlist name-and-date-of-birth match
    def test_21_watchlist_name_and_dob_match(self):
        # 'VIKRAM SINGH' / '1985-11-20' is seeded on watchlist
        payload = {
            "document_type": "passport",
            "nationality": "IND",
            "name": "VIKRAM SINGH",
            "passport_number": "M8392104",
            "date_of_birth": "1985-11-20",
            "date_of_expiry": "2030-05-10"
        }
        report = self.engine.validate(payload, validation_date=self.ref_date)
        self.assertEqual(report.overall_status, ValidationStatus.FAIL)
        self.assertIn(ValidationFlag.IDENTITY_ON_WATCHLIST.value, report.flags)

    # 22. Duplicate identity with multiple document numbers
    def test_22_duplicate_identity_with_multiple_document_numbers(self):
        # ELENA ROSTOVA / 1990-07-15 is seeded with 3 distinct document numbers
        payload = {
            "document_type": "passport",
            "nationality": "FRA",
            "name": "ELENA ROSTOVA",
            "passport_number": "F9999000",  # A new 4th number for same person
            "date_of_birth": "1990-07-15",
            "date_of_expiry": "2031-01-01"
        }
        report = self.engine.validate(payload, validation_date=self.ref_date)
        self.assertTrue(report.validation_results["duplicate_identity_found"])
        self.assertIn(ValidationFlag.DUPLICATE_IDENTITY_FOUND.value, report.flags)
        self.assertIn(ValidationFlag.MULTIPLE_DOCUMENT_NUMBERS.value, report.flags)

    # 23. Unknown country
    def test_23_unknown_country(self):
        payload = {
            "document_type": "passport",
            "nationality": "XYZ",  # Unsupported ISO code
            "name": "CITIZEN X",
            "passport_number": "XYZ12345",
            "date_of_birth": "1995-01-01",
            "date_of_expiry": "2030-01-01"
        }
        report = self.engine.validate(payload, validation_date=self.ref_date)
        self.assertIn(ValidationFlag.UNSUPPORTED_STANDARD.value, report.flags)
        self.assertIn(ValidationFlag.LOW_CONFIDENCE_STANDARD.value, report.flags)

    # 24. Unknown document type
    def test_24_unknown_document_type(self):
        payload = {
            "document_type": "diplomatic_scroll",
            "nationality": "IND",
            "name": "EMBASSY COURIER",
            "document_number": "SCROLL-99",
            "date_of_birth": "1980-01-01"
        }
        report = self.engine.validate(payload, validation_date=self.ref_date)
        self.assertIn(ValidationFlag.UNSUPPORTED_STANDARD.value, report.flags)

    # 25. Unsupported standard
    def test_25_unsupported_standard(self):
        payload = {
            "document_type": "special_entry_token",
            "country_code": "UTOPIA",
            "name": "TRAVELER ONE",
            "document_number": "TOK12345",
            "date_of_birth": "1995-01-01"
        }
        report = self.engine.validate(payload, validation_date=self.ref_date)
        self.assertIn(ValidationFlag.UNSUPPORTED_STANDARD.value, report.flags)

    # 26. Empty database
    def test_26_empty_database(self):
        empty_db_path = os.path.join(self.test_dir.name, "empty_border.db")
        # Initialize schema without data
        import sqlite3
        conn = sqlite3.connect(empty_db_path)
        try:
            conn.execute("CREATE TABLE blacklist_documents (document_number TEXT, country_code TEXT, reason TEXT, date_added TEXT, status TEXT, source_label TEXT)")
            conn.execute("CREATE TABLE watchlist_identities (name TEXT, date_of_birth TEXT, nationality TEXT, reason TEXT, date_added TEXT, status TEXT, source_label TEXT)")
            conn.execute("CREATE TABLE registered_documents (document_number TEXT, document_type TEXT, name TEXT, date_of_birth TEXT, nationality TEXT, date_of_expiry TEXT, date_registered TEXT, status TEXT)")
            conn.commit()
        finally:
            conn.close()
        
        cfg = ValidationConfig(db_path=empty_db_path, validation_date=self.ref_date)
        eng = DocumentValidationEngine(config=cfg)
        payload = {
            "document_type": "national_id",
            "country_code": "USA",
            "name": "TEST CLEAN",
            "national_id_number": "ID847291",
            "date_of_birth": "1990-01-01"
        }
        report = eng.validate(payload, validation_date=self.ref_date)
        self.assertFalse(report.validation_results["on_blacklist"])
        self.assertEqual(report.overall_status, ValidationStatus.PASS)

    # 27. Database connection failure
    def test_27_database_connection_failure(self):
        non_existent_db = os.path.join(self.test_dir.name, "does_not_exist.db")
        repo = BorderSecurityRepository(non_existent_db)
        res = repo.check_blacklist("M8392104")
        self.assertFalse(res.hit)
        self.assertIsNotNone(res.error)

    # 28. Malformed configuration
    def test_28_malformed_configuration(self):
        # Validation with non-dict input
        report = self.engine.validate("MALFORMED_STRING_PAYLOAD", validation_date=self.ref_date)
        self.assertEqual(report.overall_status, ValidationStatus.INCOMPLETE)
        self.assertIn(ValidationFlag.INVALID_FIELD_TYPE.value, report.flags)

    # 29. Repeated deterministic validation
    def test_29_repeated_deterministic_validation(self):
        payload = {
            "document_type": "passport",
            "nationality": "IND",
            "name": "RAHUL SHARMA",
            "passport_number": "M8392104",
            "date_of_birth": "1995-04-12",
            "date_of_expiry": "2032-08-20",
            "mrz_line_1": "P<INDSHARMA<<RAHUL<<<<<<<<<<<<<<<<<<<<<<<<<<",
            "mrz_line_2": "M8392104<3IND9504121M3208209<<<<<<<<<<<<<<<4",
            "mrz_checksum_score": 0.95,
            "ocr_confidence": 0.98
        }
        reports = [self.engine.validate(payload, validation_date=self.ref_date) for _ in range(5)]
        first_dict = reports[0].to_dict()
        for r in reports[1:]:
            r_dict = r.to_dict()
            self.assertEqual(first_dict["overall_status"], r_dict["overall_status"])
            self.assertEqual(first_dict["flags"], r_dict["flags"])
            self.assertEqual(first_dict["validation_results"], r_dict["validation_results"])

    # 30. Privacy masking behavior
    def test_30_privacy_masking_behavior(self):
        payload = {
            "document_type": "passport",
            "nationality": "IND",
            "name": "CONFIDENTIAL TRAVELER",
            "passport_number": "M8392104",
            "date_of_birth": "1995-04-12",
            "date_of_expiry": "2032-08-20"
        }
        report = self.engine.validate(payload, validation_date=self.ref_date)
        # Check that document_number in top-level report is masked
        self.assertEqual(report.document_number, "M8*****4")
        self.assertNotIn("M8392104", report.document_number)


if __name__ == "__main__":
    unittest.main()
