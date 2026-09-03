"""
ICAO Doc 9303 MRZ (Machine Readable Zone) validator and check-digit engine.
"""
from typing import Any, Dict, List, Optional, Tuple
import re

from document_validation.core.normalizer import NormalizedInput
from document_validation.core.privacy import mask_document_number, mask_name
from document_validation.core.rule_registry import DocumentRule
from document_validation.models.flags import ValidationFlag
from document_validation.models.result_model import CheckStatus, FieldResult
from document_validation.validators.base import BaseValidator


def icao_char_value(c: str) -> int:
    """ICAO Doc 9303 character values: '<' is 0, 0-9 is 0-9, A-Z is 10-35."""
    if c == "<":
        return 0
    if c.isdigit():
        return int(c)
    if "A" <= c <= "Z":
        return ord(c) - ord("A") + 10
    return 0


def calculate_icao_check_digit(data: str) -> str:
    """Calculates check digit using standard 7-3-1 weight algorithm."""
    weights = [7, 3, 1]
    total = 0
    for i, ch in enumerate(data):
        total += icao_char_value(ch) * weights[i % 3]
    return str(total % 10)


class MRZValidator(BaseValidator):
    """
    Validates ICAO Doc 9303 MRZ structure, 7-3-1 check digits,
    and cross-checks extracted MRZ fields against OCR inputs.
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

        mrz_lines = norm_input.mrz_lines
        masked_num = mask_document_number(norm_input.document_number)

        # 1. Availability check
        if not mrz_lines:
            if rule.requires_mrz:
                flags.append(ValidationFlag.MRZ_UNAVAILABLE)
                flags.append(ValidationFlag.INCOMPLETE_DATA)
                results.append(FieldResult(
                    check_name="mrz_availability_check",
                    status=CheckStatus.UNKNOWN,
                    rule_id="MRZ_AVAIL_01",
                    reason=f"MRZ is required for '{rule.document_type}' but no MRZ lines were provided in OCR data.",
                    evidence={"requires_mrz": True},
                    deterministic=True
                ))
                explanations.append(f"MRZ data unavailable for {rule.document_type} (cannot complete ICAO checksum verification).")
            return results, flags, explanations

        # 2. Structural Line Count & Length Check (TD3 standard: 2 lines of 44 characters)
        if len(mrz_lines) != 2:
            flags.append(ValidationFlag.MRZ_STRUCTURE_INVALID)
            results.append(FieldResult(
                check_name="mrz_structure_check",
                status=CheckStatus.FAIL,
                rule_id="MRZ_STRUCT_LINES",
                reason=f"MRZ line count invalid: expected 2 lines for TD3 passport, received {len(mrz_lines)}.",
                evidence={"line_count": len(mrz_lines)},
                deterministic=True
            ))
            explanations.append(f"Invalid MRZ structure: expected 2 lines, found {len(mrz_lines)}.")
            return results, flags, explanations

        line1 = mrz_lines[0].strip().upper()
        line2 = mrz_lines[1].strip().upper()

        if len(line1) != 44 or len(line2) != 44:
            flags.append(ValidationFlag.MRZ_STRUCTURE_INVALID)
            results.append(FieldResult(
                check_name="mrz_length_check",
                status=CheckStatus.FAIL,
                rule_id="MRZ_STRUCT_LEN",
                reason=f"MRZ line length mismatch: Line 1 has {len(line1)} chars, Line 2 has {len(line2)} chars (expected exactly 44 each).",
                evidence={"line1_len": len(line1), "line2_len": len(line2)},
                deterministic=True
            ))
            explanations.append(f"Invalid MRZ line length: Line 1 ({len(line1)}), Line 2 ({len(line2)}) - must be 44 chars each.")
            return results, flags, explanations

        # Check permitted character set
        mrz_pattern = r"^[A-Z0-9<]{44}$"
        if not re.match(mrz_pattern, line1) or not re.match(mrz_pattern, line2):
            flags.append(ValidationFlag.MRZ_STRUCTURE_INVALID)
            results.append(FieldResult(
                check_name="mrz_charset_check",
                status=CheckStatus.FAIL,
                rule_id="MRZ_CHARSET_01",
                reason="MRZ lines contain invalid characters outside ICAO Doc 9303 alphabet [A-Z0-9<].",
                evidence={},
                deterministic=True
            ))
            explanations.append("MRZ contains invalid characters outside the allowed ICAO [A-Z0-9<] set.")
            return results, flags, explanations

        results.append(FieldResult(
            check_name="mrz_structure_check",
            status=CheckStatus.PASS,
            rule_id="MRZ_STRUCT_OK",
            reason="MRZ conforms structurally to ICAO Doc 9303 TD3 specifications (2 lines, 44 chars each).",
            evidence={"format": "TD3"},
            deterministic=True
        ))

        # 3. Check Digit Verifications (ICAO Doc 9303 TD3)
        # Line 2 components:
        # 0:9   -> Document number (9 chars)
        # 9     -> Document number check digit
        # 10:13 -> Nationality (3 chars)
        # 13:19 -> Date of birth YYMMDD (6 chars)
        # 19    -> Date of birth check digit
        # 20    -> Sex
        # 21:27 -> Date of expiry YYMMDD (6 chars)
        # 27    -> Date of expiry check digit
        # 28:42 -> Optional personal number data (14 chars)
        # 42    -> Optional data check digit
        # 43    -> Composite check digit

        mrz_doc_num_field = line2[0:9]
        mrz_doc_num_cd = line2[9]
        calc_doc_cd = calculate_icao_check_digit(mrz_doc_num_field)

        mrz_dob_field = line2[13:19]
        mrz_dob_cd = line2[19]
        calc_dob_cd = calculate_icao_check_digit(mrz_dob_field)

        mrz_exp_field = line2[21:27]
        mrz_exp_cd = line2[27]
        calc_exp_cd = calculate_icao_check_digit(mrz_exp_field)

        mrz_opt_field = line2[28:42]
        mrz_opt_cd = line2[42]

        # Composite check digit data in TD3:
        # Line 2: (0..10) + (13..20) + (21..43)
        composite_data = line2[0:10] + line2[13:20] + line2[21:43]
        mrz_composite_cd = line2[43]
        calc_composite_cd = calculate_icao_check_digit(composite_data)

        # Check 3.1: Document Number Check Digit
        if calc_doc_cd != mrz_doc_num_cd:
            flags.append(ValidationFlag.MRZ_CHECKSUM_INVALID)
            results.append(FieldResult(
                check_name="mrz_doc_number_checksum",
                status=CheckStatus.FAIL,
                rule_id="ICAO_CD_DOCNUM",
                reason=f"Document number MRZ check digit failed (expected '{calc_doc_cd}', found '{mrz_doc_num_cd}').",
                evidence={"expected": calc_doc_cd, "found": mrz_doc_num_cd},
                deterministic=True
            ))
            explanations.append(f"MRZ document number check digit mismatch: mathematical check failed.")
        else:
            results.append(FieldResult(
                check_name="mrz_doc_number_checksum",
                status=CheckStatus.PASS,
                rule_id="ICAO_CD_DOCNUM",
                reason=f"Document number check digit is mathematically valid ('{mrz_doc_num_cd}').",
                evidence={"check_digit": mrz_doc_num_cd},
                deterministic=True
            ))

        # Check 3.2: Date of Birth Check Digit
        if calc_dob_cd != mrz_dob_cd:
            flags.append(ValidationFlag.MRZ_CHECKSUM_INVALID)
            results.append(FieldResult(
                check_name="mrz_dob_checksum",
                status=CheckStatus.FAIL,
                rule_id="ICAO_CD_DOB",
                reason=f"Date of birth MRZ check digit failed (expected '{calc_dob_cd}', found '{mrz_dob_cd}').",
                evidence={"expected": calc_dob_cd, "found": mrz_dob_cd},
                deterministic=True
            ))
            explanations.append("MRZ date of birth check digit mismatch: mathematical check failed.")
        else:
            results.append(FieldResult(
                check_name="mrz_dob_checksum",
                status=CheckStatus.PASS,
                rule_id="ICAO_CD_DOB",
                reason=f"Date of birth check digit is mathematically valid ('{mrz_dob_cd}').",
                evidence={"check_digit": mrz_dob_cd},
                deterministic=True
            ))

        # Check 3.3: Expiry Date Check Digit
        if calc_exp_cd != mrz_exp_cd:
            flags.append(ValidationFlag.MRZ_CHECKSUM_INVALID)
            results.append(FieldResult(
                check_name="mrz_expiry_checksum",
                status=CheckStatus.FAIL,
                rule_id="ICAO_CD_EXP",
                reason=f"Expiry date MRZ check digit failed (expected '{calc_exp_cd}', found '{mrz_exp_cd}').",
                evidence={"expected": calc_exp_cd, "found": mrz_exp_cd},
                deterministic=True
            ))
            explanations.append("MRZ expiry date check digit mismatch: mathematical check failed.")
        else:
            results.append(FieldResult(
                check_name="mrz_expiry_checksum",
                status=CheckStatus.PASS,
                rule_id="ICAO_CD_EXP",
                reason=f"Expiry date check digit is mathematically valid ('{mrz_exp_cd}').",
                evidence={"check_digit": mrz_exp_cd},
                deterministic=True
            ))

        # Check 3.4: Composite Check Digit
        if calc_composite_cd != mrz_composite_cd:
            flags.append(ValidationFlag.MRZ_COMPOSITE_CHECKSUM_INVALID)
            flags.append(ValidationFlag.MRZ_CHECKSUM_INVALID)
            results.append(FieldResult(
                check_name="mrz_composite_checksum",
                status=CheckStatus.FAIL,
                rule_id="ICAO_CD_COMPOSITE",
                reason=f"MRZ composite check digit failed (expected '{calc_composite_cd}', found '{mrz_composite_cd}').",
                evidence={"expected": calc_composite_cd, "found": mrz_composite_cd},
                deterministic=True
            ))
            explanations.append("MRZ composite check digit mismatch: document data integrity validation failed.")
        else:
            results.append(FieldResult(
                check_name="mrz_composite_checksum",
                status=CheckStatus.PASS,
                rule_id="ICAO_CD_COMPOSITE",
                reason=f"MRZ composite check digit is mathematically valid ('{mrz_composite_cd}').",
                evidence={"check_digit": mrz_composite_cd},
                deterministic=True
            ))

        # 4. Cross-Verification: Compare MRZ extracted fields against OCR structured input
        mrz_clean_doc_num = mrz_doc_num_field.replace("<", "").strip().upper()
        if norm_input.document_number and mrz_clean_doc_num != norm_input.document_number:
            flags.append(ValidationFlag.MRZ_DOCUMENT_NUMBER_MISMATCH)
            results.append(FieldResult(
                check_name="mrz_doc_number_crosscheck",
                status=CheckStatus.FAIL,
                rule_id="CROSS_DOCNUM_01",
                reason=f"Document number mismatch: OCR gave '{masked_num}', but MRZ contains '{mask_document_number(mrz_clean_doc_num)}'.",
                evidence={"ocr_doc_num": masked_num, "mrz_doc_num": mask_document_number(mrz_clean_doc_num)},
                deterministic=True
            ))
            explanations.append(f"Discrepancy detected between OCR document number ({masked_num}) and MRZ value.")
        else:
            results.append(FieldResult(
                check_name="mrz_doc_number_crosscheck",
                status=CheckStatus.PASS,
                rule_id="CROSS_DOCNUM_OK",
                reason="Document number matches between OCR text and MRZ zone.",
                evidence={"matched": True},
                deterministic=True
            ))

        # Cross-check DOB
        if norm_input.dates.dob:
            expected_dob_mrz = norm_input.dates.dob.strftime("%y%m%d")
            if expected_dob_mrz != mrz_dob_field:
                flags.append(ValidationFlag.MRZ_DATE_OF_BIRTH_MISMATCH)
                results.append(FieldResult(
                    check_name="mrz_dob_crosscheck",
                    status=CheckStatus.FAIL,
                    rule_id="CROSS_DOB_01",
                    reason=f"Date of birth mismatch: OCR indicates '{norm_input.dates.dob.isoformat()}', but MRZ has '{mrz_dob_field}'.",
                    evidence={"mrz_dob": mrz_dob_field},
                    deterministic=True
                ))
                explanations.append("Discrepancy detected between OCR date of birth and MRZ date of birth.")
            else:
                results.append(FieldResult(
                    check_name="mrz_dob_crosscheck",
                    status=CheckStatus.PASS,
                    rule_id="CROSS_DOB_OK",
                    reason="Date of birth matches between OCR and MRZ.",
                    evidence={"matched": True},
                    deterministic=True
                ))

        # Cross-check Expiry
        if norm_input.dates.expiry_date:
            expected_exp_mrz = norm_input.dates.expiry_date.strftime("%y%m%d")
            if expected_exp_mrz != mrz_exp_field:
                flags.append(ValidationFlag.MRZ_EXPIRY_DATE_MISMATCH)
                results.append(FieldResult(
                    check_name="mrz_expiry_crosscheck",
                    status=CheckStatus.FAIL,
                    rule_id="CROSS_EXP_01",
                    reason=f"Expiry date mismatch: OCR indicates '{norm_input.dates.expiry_date.isoformat()}', but MRZ has '{mrz_exp_field}'.",
                    evidence={"mrz_exp": mrz_exp_field},
                    deterministic=True
                ))
                explanations.append("Discrepancy detected between OCR expiry date and MRZ expiry date.")
            else:
                results.append(FieldResult(
                    check_name="mrz_expiry_crosscheck",
                    status=CheckStatus.PASS,
                    rule_id="CROSS_EXP_OK",
                    reason="Expiry date matches between OCR and MRZ.",
                    evidence={"matched": True},
                    deterministic=True
                ))

        # Cross-check Name
        if norm_input.name:
            # MRZ line 1 name format: starts at char index 5: SURNAME<<GIVEN<NAMES
            mrz_name_part = line1[5:].replace("<", " ").strip()
            ocr_tokens = [tok for tok in norm_input.name.upper().split() if len(tok) >= 2]
            name_mismatch = any(tok not in mrz_name_part for tok in ocr_tokens)
            if name_mismatch and len(ocr_tokens) > 0:
                results.append(FieldResult(
                    check_name="mrz_name_crosscheck",
                    status=CheckStatus.WARN,
                    rule_id="CROSS_NAME_WARN",
                    reason=f"Potential name discrepancy between OCR '{mask_name(norm_input.name)}' and MRZ name area.",
                    evidence={"masked_name": mask_name(norm_input.name)},
                    deterministic=True
                ))
            else:
                results.append(FieldResult(
                    check_name="mrz_name_crosscheck",
                    status=CheckStatus.PASS,
                    rule_id="CROSS_NAME_OK",
                    reason="Holder name corresponds between OCR text and MRZ line.",
                    evidence={},
                    deterministic=True
                ))

        # 5. Separation of Confidence vs Checksum
        # Check OCR and MRZ confidence scores if provided
        ocr_conf = norm_input.original.ocr_confidence
        mrz_conf = norm_input.original.mrz_checksum_score

        if mrz_conf is not None:
            # Support either 0.0-1.0 or 0-100 scale
            normalized_mrz_conf = mrz_conf / 100.0 if mrz_conf > 1.0 else mrz_conf
            if normalized_mrz_conf < 0.80:
                flags.append(ValidationFlag.LOW_MRZ_CONFIDENCE)
                results.append(FieldResult(
                    check_name="mrz_recognition_confidence",
                    status=CheckStatus.WARN,
                    rule_id="CONF_MRZ_LOW",
                    reason=f"MRZ OCR extraction confidence is low ({round(normalized_mrz_conf * 100, 1)}% < 80.0%). Mathematical checksum may be unreliably recognized.",
                    evidence={"mrz_confidence": round(normalized_mrz_conf, 2)},
                    deterministic=True
                ))
                explanations.append(f"Low MRZ recognition confidence score ({round(normalized_mrz_conf * 100, 1)}%). Manual review advised.")
            else:
                results.append(FieldResult(
                    check_name="mrz_recognition_confidence",
                    status=CheckStatus.PASS,
                    rule_id="CONF_MRZ_OK",
                    reason=f"MRZ OCR extraction confidence is sufficient ({round(normalized_mrz_conf * 100, 1)}%).",
                    evidence={"mrz_confidence": round(normalized_mrz_conf, 2)},
                    deterministic=True
                ))

        if ocr_conf is not None:
            normalized_ocr_conf = ocr_conf / 100.0 if ocr_conf > 1.0 else ocr_conf
            if normalized_ocr_conf < 0.70:
                flags.append(ValidationFlag.LOW_OCR_CONFIDENCE)
                results.append(FieldResult(
                    check_name="ocr_text_confidence",
                    status=CheckStatus.WARN,
                    rule_id="CONF_OCR_LOW",
                    reason=f"Overall OCR character recognition confidence is low ({round(normalized_ocr_conf * 100, 1)}%).",
                    evidence={"ocr_confidence": round(normalized_ocr_conf, 2)},
                    deterministic=True
                ))

        return results, flags, explanations
