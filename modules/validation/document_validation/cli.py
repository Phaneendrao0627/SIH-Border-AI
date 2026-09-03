"""
Command-Line Interface (CLI) for Module 2: Document Validation.
Allows standalone JSON file validation, mock DB seeding, and live demonstrations.
"""
import argparse
import json
import sys
from datetime import date
from typing import Optional

from document_validation.config import ValidationConfig
from document_validation.database.seeder import seed_mock_database
from document_validation.engine import DocumentValidationEngine


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Module 2: Document Validation Engine (SIH26188)"
    )
    parser.add_argument(
        "--input", "-i",
        help="Path to structured document JSON file to validate."
    )
    parser.add_argument(
        "--date", "-d",
        help="Explicit validation date (YYYY-MM-DD). Defaults to current date."
    )
    parser.add_argument(
        "--db",
        help="Path to SQLite border database."
    )
    parser.add_argument(
        "--seed",
        action="store_true",
        help="Initialize and seed the mock border security SQLite database."
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run validation on built-in demonstration cases."
    )

    args = parser.parse_args(argv)

    config = ValidationConfig()
    if args.db:
        config.db_path = args.db

    if args.seed:
        print(f"[*] Seeding mock border security database at: {config.db_path}")
        seed_mock_database(config.db_path)
        print("[+] Mock database seeded successfully.")
        return 0

    engine = DocumentValidationEngine(config=config)

    if args.demo:
        demo_docs = [
            {
                "title": "Valid Indian Passport",
                "payload": {
                    "document_type": "passport",
                    "nationality": "IND",
                    "name": "RAHUL SHARMA",
                    "passport_number": "M8392104",
                    "dob": "1995-04-12",
                    "date_of_expiry": "2032-08-20",
                    "mrz_line_1": "P<INDSHARMA<<RAHUL<<<<<<<<<<<<<<<<<<<<<<<<<<",
                    "mrz_line_2": "M8392104<3IND9504121M3208209<<<<<<<<<<<<<<<4",
                    "mrz_checksum_score": 0.95,
                    "ocr_confidence": 0.98
                }
            },
            {
                "title": "Blacklisted Passport",
                "payload": {
                    "document_type": "passport",
                    "nationality": "IND",
                    "name": "ARAVIND SWAMY",
                    "passport_number": "X9988776",
                    "dob": "1991-03-10",
                    "date_of_expiry": "2029-05-10"
                }
            },
            {
                "title": "Expired Passport",
                "payload": {
                    "document_type": "passport",
                    "nationality": "IND",
                    "name": "PRIYA SHARMA",
                    "passport_number": "C9876543",
                    "dob": "2000-08-25",
                    "date_of_expiry": "2020-08-15"
                }
            }
        ]

        print("\n" + "=" * 60)
        print(" MODULE 2: DOCUMENT VALIDATION DEMONSTRATION")
        print("=" * 60)

        for case in demo_docs:
            print(f"\n[CASE] {case['title']}")
            report = engine.validate(case["payload"], validation_date=date(2026, 9, 3))
            print(f"Status: {report.overall_status.value} (Confidence: {report.overall_confidence})")
            print(f"Flags:  {report.flags}")
            print("Explanations:")
            for exp in report.explanations:
                print(f"  - {exp}")
            print("-" * 60)
        return 0

    if not args.input:
        parser.print_help()
        return 1

    try:
        with open(args.input, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading input file '{args.input}': {e}", file=sys.stderr)
        return 2

    report = engine.validate(data, validation_date=args.date)
    print(json.dumps(report.to_dict(), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
