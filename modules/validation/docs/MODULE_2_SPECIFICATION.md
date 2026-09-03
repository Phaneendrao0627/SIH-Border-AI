# Module 2: Document Validation — System Architecture & Integration Specification

**Project**: AI-Based Fake Identity & Document Screening System (SIH26188)  
**Module**: Module 2 (Document Validation Engine)  
**Version**: `2.0.0`  
**License / Mode**: Production-Quality Hackathon Prototype / Open Architecture  

---

## 1. Module Purpose & Limitations

### 1.1 Purpose
Module 2 is an independent, rule-based, deterministic, and fully explainable document verification component situated immediately downstream of **Module 1 (OCR Extraction)**. While Module 1 answers *"What text does this document contain?"* and Module 3 investigates *"Was this document image digitally tampered with?"*, Module 2 determines:
> *"Does the structured document data follow the official syntactic, mathematical, chronological, and security database rules of real travel and identity documents?"*

The module validates format patterns, enforces logical date consistency, verifies mathematical check digits (ICAO Doc 9303 7-3-1 weights), queries local simulated blacklists/watchlists, and detects multi-document identity duplication.

### 1.2 Limitations & Explicit Exclusions
To maintain strict separation of concerns, the following features are **explicitly out of scope** for Module 2:
- **No Image Processing / OCR**: Module 2 never touches raw image files, pixels, or tesseract pipelines.
- **No Tampering Analysis**: Optical alterations, font irregularities, copy-paste seams, or stamp forgeries are handled exclusively by Module 3.
- **No Biometrics / Face Matching**: Photo-to-person or face embeddings are handled exclusively by Module 4.
- **No Final Risk Scoring**: Module 2 outputs discrete pass/fail/warn results and machine-readable flags; the subsequent Risk Scoring Engine calculates numerical risk weights.
- **No Real Government Database Connection**: All watchlist and blacklist queries utilize a local synthetic SQLite mock database. Clean local database lookups **never** constitute proof of official government authenticity.
- **No Legal / Immigration Determinations**: Outputs serve strictly as explainable decision support for authorized border-security personnel.

---

## 2. Installation & Execution Requirements

### 2.1 Runtime Environment
- **Language**: Python 3.9+ (Tested on Python 3.13)
- **External Dependencies**: **Zero** (`0` pip dependencies). Built entirely upon standard library packages:
  - `dataclasses`, `datetime`, `re`, `sqlite3`, `hashlib`, `json`, `unittest`, `argparse`.
- **Operating Systems**: Windows, Linux, macOS.

### 2.2 Quick Start Invocation
```bash
# 1. Seed the local mock database with synthetic records
python -m document_validation.cli --seed

# 2. Run built-in demonstration cases
python -m document_validation.cli --demo

# 3. Validate a structured JSON document file
python -m document_validation.cli --input docs/contract_examples/valid_passport.json

# 4. Execute the automated test suite
python -m unittest discover -s tests -p "test_*.py" -v

# 5. Generate the precision and evaluation report
python tests/run_test_report.py
```

---

## 3. Input Contract (JSON Schema & Field Definitions)

### 3.1 Input Schema
The module accepts a single JSON dictionary containing structured OCR output:

```json
{
  "request_id": "REQ-2026-0091",
  "document_type": "passport",
  "country_code": "IND",
  "name": "RAHUL SHARMA",
  "document_number": "M8392104",
  "date_of_birth": "1995-04-12",
  "date_of_issue": "2022-08-20",
  "date_of_expiry": "2032-08-20",
  "gender": "M",
  "visa_type": null,
  "entry_validity": null,
  "stay_duration": null,
  "mrz_line_1": "P<INDSHARMA<<RAHUL<<<<<<<<<<<<<<<<<<<<<<<<<<",
  "mrz_line_2": "M8392104<3IND9504121M3208209<<<<<<<<<<<<<<<4",
  "mrz_checksum_score": 0.95,
  "ocr_confidence": 0.98,
  "metadata": {
    "terminal": "GATE-02"
  }
}
```

### 3.2 Field Definitions & Fallback Aliases
| Field Name | Type | Mandatory? | Aliases / Accepted Keys | Description |
|---|---|---|---|---|
| `document_type` | `str` | Yes | - | Category: `passport`, `visa`, `national_id`, `driving_licence`, `permit`. |
| `country_code` | `str` | Yes | `nationality` | ISO 3166-1 alpha-3 code (e.g., `IND`, `USA`, `FRA`) or issuing authority. |
| `name` | `str` | Yes | - | Full legal name of the document holder. |
| `document_number`| `str` | Yes | `passport_number`, `visa_number`, `national_id_number` | Unique alphanumeric document identifier. |
| `date_of_birth` | `str` | Yes | `dob` | Date of birth in accepted calendar formats (`YYYY-MM-DD`, `DD-MM-YYYY`). |
| `date_of_issue` | `str` | Conditional | `issue_date` | Date document was issued (mandatory for visas and driving licences). |
| `date_of_expiry`| `str` | Conditional | `expiry` | Expiration date (mandatory for passports, visas, driving licences). |
| `gender` | `str` | Optional | `sex` | Holder gender: `M`, `F`, `X`. |
| `visa_type` | `str` | Optional | - | Visa classification (e.g. `B1/B2`, `TOURIST`, `WORK`). |
| `stay_duration` | `str/int` | Optional | - | Authorized stay duration (e.g. `90`, `"90 days"`). |
| `mrz_line_1` | `str` | Conditional | `mrz` (line 1) | First line of Machine Readable Zone (44 characters for TD3 passports). |
| `mrz_line_2` | `str` | Conditional | `mrz` (line 2) | Second line of Machine Readable Zone (44 characters for TD3 passports). |
| `mrz_checksum_score` | `float` | Optional | `valid_score` | Confidence score from OCR MRZ reader (`0.0 - 1.0` or `0 - 100`). |
| `ocr_confidence`| `float` | Optional | - | General OCR character recognition confidence (`0.0 - 1.0`). |
| `request_id` | `str` | Optional | - | Client tracking UUID; auto-generated if omitted. |

---

## 4. Output Contract (JSON Schema & Result Model)

### 4.1 Output Structure
```json
{
  "request_id": "REQ-2026-0091",
  "document_type": "passport",
  "document_number": "M8*****4",
  "validation_timestamp": "2026-09-03T22:46:46.540702",
  "validation_date": "2026-09-03",
  "overall_status": "PASS",
  "overall_confidence": 1.0,
  "validation_results": {
    "format_valid": true,
    "date_logic_valid": true,
    "not_expired": true,
    "mrz_checksum_valid": true,
    "on_blacklist": false,
    "duplicate_identity_found": false,
    "standards_compliant": true
  },
  "flags": [
    "STANDARDS_COMPLIANT"
  ],
  "explanations": [
    "All structural, date logic, checksum, and blacklist checks passed successfully."
  ],
  "field_results": [
    {
      "check_name": "mrz_composite_checksum",
      "status": "PASS",
      "rule_id": "ICAO_CD_COMPOSITE",
      "reason": "MRZ composite check digit is mathematically valid ('4').",
      "evidence": {
        "check_digit": "4"
      },
      "deterministic": true
    }
  ],
  "database_results": {
    "blacklist_checked": true,
    "blacklist_hit": false,
    "blacklist_details": null,
    "watchlist_checked": true,
    "watchlist_hit": false,
    "watchlist_details": null,
    "duplicate_checked": true,
    "duplicate_found": false,
    "duplicate_count": 0,
    "duplicate_details": null,
    "disclaimer": "Clean local mock database lookup does NOT verify official authenticity. Intended for decision support only."
  },
  "standards_checked": [
    "ICAO Doc 9303 Part 4 (TD3)"
  ],
  "validator_version": "2.0.0",
  "warnings": [],
  "errors": []
}
```

### 4.2 Overall Status Determination Logic
Overall status is assigned using strict deterministic rules:
- **`FAIL`**: Triggered when a critical security or structural defect is detected:
  - Document number is blacklisted.
  - Person's identity is on border watchlist.
  - MRZ mathematical check digits fail (tampered digits).
  - MRZ extracted data contradicts OCR text (data mismatch).
  - Document is expired relative to validation date.
  - Inverted or impossible dates (future DOB, future issue date, expiry before issue).
  - Prohibited characters, invalid country pattern, or suspicious placeholder (`00000000`, `12345678`).
- **`INCOMPLETE`**: Triggered when validation cannot safely complete:
  - Missing mandatory fields (`document_number`, `name`, `date_of_birth`, etc.).
  - MRZ is required for the document type (e.g. passport) but absent from input.
- **`WARN`**: Triggered when the document passes available rules, but exhibits non-critical risks:
  - Document is close to expiration (`EXPIRING_SOON`, within 180 days).
  - Duplicate identity detected under multiple document numbers.
  - Low OCR character confidence (< 70%) or low MRZ score (< 80%).
  - Unsupported country standard (fallback generic rules applied).
  - Database lookup inconclusive / temporarily unavailable.
- **`PASS`**: Granted **only** when all required checks succeed with zero critical warnings or failures.

---

## 5. Validation Checks Performed

### 5.1 Document Format & Regex Validation
- Enforces official national formats (e.g., Indian Passports: `^[A-Z][0-9]{7}$`, exact length 8).
- Prohibits non-alphanumeric symbols (`#`, `@`, `$`, `%`, `*`).
- Detects repetitive or sequential placeholder numbers (`00000000`, `12345678`, `XXXXXXXX`, `TEST`, `SAMPLE`).

### 5.2 Date Logic & Chronological Validation
- **Calendar Integrity**: Correct handling of leap years (e.g., `2024-02-29` is valid, `2023-02-29` fails).
- **Date of Birth**: Must be in the past. Calculated age must be realistic (0 to 130 years).
- **Date of Issue**: Must not be in the future, and must not precede the holder's date of birth.
- **Date of Expiry**: Must be strictly after the date of issue (`expiry <= issue` triggers `EXPIRY_BEFORE_ISSUE`).
- **Visa Validity**: Declared stay duration (e.g., 90 days) must not exceed total validity window (`expiry - issue`).

### 5.3 ICAO Doc 9303 MRZ Verification (Passports)
- **Geometry**: Evaluates TD3 passport format (2 lines, exactly 44 characters per line).
- **Character Alphabet**: Must strictly conform to `[0-9A-Z<]`.
- **7-3-1 Weight Algorithm**: Calculates mathematical modulus-10 check digits using weights `[7, 3, 1]`:
  $$\text{Check Digit} = \left(\sum_{i=0}^{n-1} \text{Value}(c_i) \times W_{i \pmod 3}\right) \pmod{10}$$
  *(Values: `<` = 0, `0-9` = 0-9, `A-Z` = 10-35).*
- **Independently Verifies**:
  1. Document Number Check Digit (Line 2, index 9)
  2. Date of Birth Check Digit (Line 2, index 19)
  3. Date of Expiry Check Digit (Line 2, index 27)
  4. Composite Check Digit (Line 2, index 43)
- **Cross-Verification**: Confirms exact agreement between OCR fields and MRZ zones.

### 5.4 Database Checks (Blacklist, Watchlist, Duplicates)
- **Blacklist Lookup**: Queries document numbers (exact & normalized) against flagged lost/stolen document registry.
- **Watchlist Lookup**: Matches demographic combinations (`Name` + `Date of Birth`) against simulated security notices.
- **Duplicate Identity Detection**: Detects individuals registered under multiple distinct document numbers. Flags `POSSIBLE_IDENTITY_COLLISION` with clear warnings that demographic homonyms require biometric verification.

---

## 6. Catalog of Flags & Errors

### 6.1 Validation Flags
| Flag Category | Flag Identifier | Meaning |
|---|---|---|
| **Input / Schema** | `MISSING_DOCUMENT_NUMBER` | Mandatory document identifier is missing or null. |
| | `MISSING_NAME` | Full name is missing or null. |
| | `MISSING_DATE_OF_BIRTH` | DOB is missing or null. |
| | `MISSING_EXPIRY_DATE` | Expiration date is missing on a document requiring it. |
| | `INVALID_FIELD_TYPE` | Non-string or malformed data type provided. |
| | `INCOMPLETE_DATA` | Required information missing; validation cannot safely complete. |
| **Format** | `INVALID_DOCUMENT_NUMBER_FORMAT` | Number does not conform to official regex. |
| | `INVALID_DOCUMENT_NUMBER_LENGTH` | Character count is outside permitted min/max range. |
| | `INVALID_DOCUMENT_NUMBER_CHARACTERS` | Number contains illegal symbols or punctuation. |
| | `COUNTRY_FORMAT_MISMATCH` | Number violates declared issuing nation's standard. |
| | `SUSPICIOUS_PLACEHOLDER_NUMBER` | Obvious sequential (`12345678`) or repeated dummy sequence. |
| **Date Logic** | `INVALID_DATE_FORMAT` | Date string cannot be parsed into a calendar date. |
| | `FUTURE_DATE_OF_BIRTH` | DOB is chronologically after the validation date. |
| | `UNREALISTIC_AGE` | Computed age exceeds 130 years. |
| | `FUTURE_ISSUE_DATE` | Document issue date is in the future. |
| | `EXPIRY_BEFORE_ISSUE` | Expiration date precedes or equals issue date. |
| | `EXPIRED_DOCUMENT` | Document has passed its expiration date. |
| | `EXPIRING_SOON` | Document expires within configured warning window (180 days). |
| | `INVALID_STAY_DURATION` | Visa authorized stay exceeds total validity span. |
| **MRZ / Checksum** | `MRZ_STRUCTURE_INVALID` | Incorrect line count or line length (not 44 characters). |
| | `MRZ_CHECKSUM_INVALID` | Mathematical check digit calculation failed. |
| | `MRZ_COMPOSITE_CHECKSUM_INVALID` | Composite data integrity check digit failed. |
| | `MRZ_DOCUMENT_NUMBER_MISMATCH` | OCR document number disagrees with MRZ data. |
| | `MRZ_DATE_OF_BIRTH_MISMATCH` | OCR birth date disagrees with MRZ data. |
| | `MRZ_EXPIRY_DATE_MISMATCH` | OCR expiration date disagrees with MRZ data. |
| | `MRZ_UNAVAILABLE` | MRZ required for document type but omitted. |
| | `LOW_MRZ_CONFIDENCE` | MRZ optical reader score is under 80%. |
| | `LOW_OCR_CONFIDENCE` | General OCR character confidence is under 70%. |
| **Database** | `DOCUMENT_ON_BLACKLIST` | Exact or normalized document number on blacklist. |
| | `IDENTITY_ON_WATCHLIST` | Name + DOB match on security watchlist. |
| | `DUPLICATE_IDENTITY_FOUND` | Same individual linked to multiple document numbers. |
| | `WATCHLIST_DATABASE_UNAVAILABLE` | Database query failed (connection or file error). |
| **Standards** | `STANDARDS_COMPLIANT` | Document structural requirements verified against ICAO/ISO. |
| | `STANDARDS_NON_COMPLIANT` | Document violates declared international standard. |
| | `UNSUPPORTED_STANDARD` | Country/document type rule not in registry; fallback applied. |

---

## 7. Privacy, Security & Data Masking

To ensure compliance with data protection principles and prevent accidental PII leakage:
1. **Identifier Masking**: Document numbers are masked in all audit logs, CLI prints, and reports:
   - `M8392104` $\rightarrow$ `M8*****4`
   - `DL99883344` $\rightarrow$ `DL******44`
2. **Name Tokenization**: Name strings are redacted in sensitive audit views (`RAHUL SHARMA` $\rightarrow$ `R**** S*****`).
3. **Pseudonymized Identity Tokens**: Duplication tracking can utilize SHA-256 identity hashes:
   $$\text{Token} = \text{SHA256}(\text{NAME} \parallel \text{DOB} \parallel \text{COUNTRY})[0:16]$$
4. **No Raw Image Retention**: Module 2 never persists or receives raw biometric imagery.

---

## 8. Integration Handoff Guide for Downstream Teams

### 8.1 Calling Module 2 in Python
Any backend service, pipeline, or scoring orchestrator can import and call Module 2 directly:

```python
from datetime import date
from document_validation.engine import DocumentValidationEngine
from document_validation.config import ValidationConfig

# 1. Initialize engine (zero configuration needed for defaults)
engine = DocumentValidationEngine()

# 2. Define OCR input payload
ocr_data = {
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

# 3. Execute validation (optionally pass explicit reference date for testing)
report = engine.validate(ocr_data, validation_date=date(2026, 9, 3))

# 4. Access structured results
print(report.overall_status.value)       # "PASS", "FAIL", "WARN", or "INCOMPLETE"
print(report.overall_confidence)         # float, e.g. 1.0
print(report.flags)                      # list of machine-readable flag strings
print(report.explanations)               # human-readable border explanations

# 5. Serialize for API / downstream message queues
json_output = report.to_dict()
```

### 8.2 Dependency Injection for Testing
```python
# Custom database path and strict expiry window
custom_config = ValidationConfig(
    db_path="/custom/path/to/border.db",
    expiring_soon_threshold_days=90,
    validation_date=date(2026, 12, 31)
)
custom_engine = DocumentValidationEngine(config=custom_config)
```
