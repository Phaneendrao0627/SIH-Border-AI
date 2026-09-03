"""
Document-number and format validator.
"""
from typing import List, Tuple
import re

from document_validation.core.normalizer import NormalizedInput
from document_validation.core.privacy import mask_document_number
from document_validation.core.rule_registry import DocumentRule
from document_validation.models.flags import ValidationFlag
from document_validation.models.result_model import CheckStatus, FieldResult
from document_validation.validators.base import BaseValidator

SUSPICIOUS_PLACEHOLDERS = [
    "0000000", "00000000", "1234567", "12345678", "123456789",
    "98765432", "11111111", "99999999", "TEST", "SAMPLE", "DEMO",
    "DUMMY", "XXXXXXX", "XXXXXXXX", "ABC12345", "A1234567"  # Note: A1234567 is often used in basic demos, but let's check exact repeated or sample keywords
]
# Specifically keyword-based or obvious repetitions:
PLACEHOLDER_KEYWORDS = ["TEST", "SAMPLE", "DEMO", "DUMMY", "VOID", "NULL", "FAKE"]


class FormatValidator(BaseValidator):
    """
    Validates mandatory field presence, document number pattern, length,
    character set, and flags suspicious placeholder numbers.
    """

    def validate(
        self,
        norm_input: NormalizedInput,
        rule: DocumentRule,
        **kwargs
    ) -> Tuple[List[FieldResult], List[ValidationFlag], List[str]]:
        results: List[FieldResult] = []
        flags: List[ValidationFlag] = []
        explanations: List[str] = []

        masked_num = mask_document_number(norm_input.document_number)

        # 1. Mandatory Fields Presence Check
        missing_mandatory: List[str] = []
        field_mapping = {
            "document_number": norm_input.document_number,
            "name": norm_input.name,
            "date_of_birth": norm_input.dates.dob,
            "country_code": norm_input.country_code,
            "date_of_expiry": norm_input.dates.expiry_date,
            "date_of_issue": norm_input.dates.issue_date,
        }

        for req_field in rule.mandatory_fields:
            val = field_mapping.get(req_field)
            if val is None or (isinstance(val, str) and not val.strip()):
                missing_mandatory.append(req_field)
                if req_field == "document_number":
                    flags.append(ValidationFlag.MISSING_DOCUMENT_NUMBER)
                elif req_field == "name":
                    flags.append(ValidationFlag.MISSING_NAME)
                elif req_field == "date_of_birth":
                    flags.append(ValidationFlag.MISSING_DATE_OF_BIRTH)
                elif req_field == "country_code":
                    flags.append(ValidationFlag.MISSING_NATIONALITY)
                elif req_field == "date_of_expiry":
                    flags.append(ValidationFlag.MISSING_EXPIRY_DATE)

        if missing_mandatory:
            flags.append(ValidationFlag.INCOMPLETE_DATA)
            results.append(FieldResult(
                check_name="mandatory_fields_check",
                status=CheckStatus.FAIL,
                rule_id="REQ_FIELDS_01",
                reason=f"Mandatory field(s) missing for document type '{rule.document_type}': {', '.join(missing_mandatory)}.",
                evidence={"missing_fields": missing_mandatory},
                deterministic=True
            ))
            explanations.append(f"Validation incomplete: missing mandatory fields ({', '.join(missing_mandatory)}).")
        else:
            results.append(FieldResult(
                check_name="mandatory_fields_check",
                status=CheckStatus.PASS,
                rule_id="REQ_FIELDS_01",
                reason="All mandatory fields for this document category are present.",
                evidence={"checked_fields": rule.mandatory_fields},
                deterministic=True
            ))

        doc_num = norm_input.document_number
        if not doc_num:
            return results, flags, explanations

        # 2. Suspicious Placeholder Check
        is_placeholder = False
        upper_num = doc_num.upper()

        for kw in PLACEHOLDER_KEYWORDS:
            if kw in upper_num:
                is_placeholder = True
                break

        # Check all identical characters (e.g. 00000000, 99999999, XXXXXXXX)
        if len(set(doc_num)) == 1 and len(doc_num) >= 4:
            is_placeholder = True

        # Check purely sequential digits like 12345678, 01234567
        digits_only = re.sub(r"\D", "", doc_num)
        if len(digits_only) >= 6:
            if digits_only in "0123456789012345" or digits_only in "98765432109876":
                is_placeholder = True

        if is_placeholder:
            flags.append(ValidationFlag.SUSPICIOUS_PLACEHOLDER_NUMBER)
            results.append(FieldResult(
                check_name="placeholder_check",
                status=CheckStatus.FAIL,
                rule_id="SEC_PLACEHOLDER_01",
                reason=f"Document number '{masked_num}' exhibits obvious placeholder or test sequence patterns.",
                evidence={"pattern": "repetitive_or_sequential"},
                deterministic=True
            ))
            explanations.append(f"Suspicious placeholder document number detected ({masked_num}).")
        else:
            results.append(FieldResult(
                check_name="placeholder_check",
                status=CheckStatus.PASS,
                rule_id="SEC_PLACEHOLDER_01",
                reason="Document number does not match known test patterns or repetitive placeholder values.",
                evidence={"masked_number": masked_num},
                deterministic=True
            ))

        # 3. Prohibited Characters Check
        # Document numbers must strictly conform to allowed alphanumeric set
        prohibited_match = re.search(r"[^A-Za-z0-9]", doc_num)
        if prohibited_match:
            flags.append(ValidationFlag.INVALID_DOCUMENT_NUMBER_CHARACTERS)
            results.append(FieldResult(
                check_name="character_set_check",
                status=CheckStatus.FAIL,
                rule_id="CHAR_VALIDITY_01",
                reason=f"Document number contains prohibited character '{prohibited_match.group(0)}'. Expected characters: {rule.allowed_characters_desc}.",
                evidence={"prohibited_char": prohibited_match.group(0)},
                deterministic=True
            ))
            explanations.append(f"Invalid character set in document number ({masked_num}).")
        else:
            results.append(FieldResult(
                check_name="character_set_check",
                status=CheckStatus.PASS,
                rule_id="CHAR_VALIDITY_01",
                reason="Document number character set is valid.",
                evidence={"allowed": rule.allowed_characters_desc},
                deterministic=True
            ))

        # 4. Length Validation
        if not (rule.min_length <= len(doc_num) <= rule.max_length):
            flags.append(ValidationFlag.INVALID_DOCUMENT_NUMBER_LENGTH)
            results.append(FieldResult(
                check_name="document_length_check",
                status=CheckStatus.FAIL,
                rule_id="LEN_VALIDITY_01",
                reason=f"Document number length {len(doc_num)} is out of bounds for {rule.rule_id} (Expected {rule.min_length}-{rule.max_length}).",
                evidence={"actual_length": len(doc_num), "expected_range": [rule.min_length, rule.max_length]},
                deterministic=True
            ))
            explanations.append(f"Document number length invalid: expected {rule.min_length}-{rule.max_length}, found {len(doc_num)}.")
        else:
            results.append(FieldResult(
                check_name="document_length_check",
                status=CheckStatus.PASS,
                rule_id="LEN_VALIDITY_01",
                reason=f"Document number length {len(doc_num)} conforms to required bounds [{rule.min_length}-{rule.max_length}].",
                evidence={"length": len(doc_num)},
                deterministic=True
            ))

        # 5. Format / Regex Pattern Validation
        pattern_valid = rule.validate_pattern(doc_num)
        if not pattern_valid:
            flags.append(ValidationFlag.INVALID_DOCUMENT_NUMBER_FORMAT)
            if rule.country_code:
                flags.append(ValidationFlag.COUNTRY_FORMAT_MISMATCH)
                reason_text = (
                    f"Document number '{masked_num}' does not match official format for "
                    f"country {rule.country_code} ({rule.allowed_characters_desc})."
                )
            else:
                reason_text = (
                    f"Document number '{masked_num}' does not match standard pattern for "
                    f"{rule.document_type} ({rule.allowed_characters_desc})."
                )

            results.append(FieldResult(
                check_name="format_pattern_check",
                status=CheckStatus.FAIL,
                rule_id=rule.rule_id,
                reason=reason_text,
                evidence={"expected_pattern": rule.doc_number_pattern},
                deterministic=True
            ))
            explanations.append(f"Document number format violation: {reason_text}")
        else:
            results.append(FieldResult(
                check_name="format_pattern_check",
                status=CheckStatus.PASS,
                rule_id=rule.rule_id,
                reason=(
                    f"Document number '{masked_num}' matches expected structural regex pattern. "
                    "Note: Pattern validation confirms structural syntax only; it does not confirm physical genuineness."
                ),
                evidence={"rule_id": rule.rule_id},
                deterministic=True
            ))

        return results, flags, explanations
