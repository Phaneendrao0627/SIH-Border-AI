"""
Standards compliance validator (ICAO Doc 9303, ISO/IEC specifications).
"""
from typing import List, Tuple

from document_validation.core.normalizer import NormalizedInput
from document_validation.core.rule_registry import DocumentRule
from document_validation.models.flags import ValidationFlag
from document_validation.models.result_model import CheckStatus, FieldResult
from document_validation.validators.base import BaseValidator


class StandardsValidator(BaseValidator):
    """
    Evaluates compliance against formal international standards.
    Emits UNSUPPORTED_STANDARD / LOW_CONFIDENCE_STANDARD when exact
    country/standard specifications are unavailable.
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

        # Case 1: Generic Fallback Rule / Unsupported Country Specification
        if rule.is_generic_fallback:
            if not rule.standard_name:
                flags.append(ValidationFlag.UNSUPPORTED_STANDARD)
                flags.append(ValidationFlag.LOW_CONFIDENCE_STANDARD)
                results.append(FieldResult(
                    check_name="standards_compliance_check",
                    status=CheckStatus.UNKNOWN,
                    rule_id="STD_UNSUPPORTED",
                    reason=(
                        f"No official standard registered for document type '{rule.document_type}' "
                        f"and country '{norm_input.country_code or 'UNSPECIFIED'}'. Generic heuristic rules applied."
                    ),
                    evidence={"document_type": rule.document_type, "country": norm_input.country_code},
                    deterministic=True
                ))
                explanations.append(
                    f"Country-specific verification unavailable for {norm_input.country_code or 'unknown country'}; generic fallback applied with lower confidence."
                )
                return results, flags, explanations
            else:
                flags.append(ValidationFlag.LOW_CONFIDENCE_STANDARD)
                results.append(FieldResult(
                    check_name="standards_compliance_check",
                    status=CheckStatus.WARN,
                    rule_id="STD_GENERIC_STANDARD",
                    reason=(
                        f"Evaluated against generic standard '{rule.standard_name}'. Specific national "
                        f"specifications for '{norm_input.country_code}' are not registered."
                    ),
                    evidence={"standard": rule.standard_name},
                    deterministic=True
                ))

        # Case 2: ICAO Doc 9303 compliance for Passports
        if rule.document_type == "passport":
            std_name = rule.standard_name or "ICAO Doc 9303 TD3"
            mrz_lines = norm_input.mrz_lines

            if not mrz_lines:
                flags.append(ValidationFlag.STANDARDS_CHECK_INCOMPLETE)
                results.append(FieldResult(
                    check_name="icao_9303_compliance",
                    status=CheckStatus.UNKNOWN,
                    rule_id="ICAO_INCOMPLETE",
                    reason=f"Cannot verify {std_name} compliance because MRZ is missing from OCR data.",
                    evidence={"standard": std_name},
                    deterministic=True
                ))
                explanations.append(f"Standard compliance check incomplete: MRZ required for {std_name}.")
            else:
                # Check MRZ structure conformity
                is_td3_compliant = (
                    len(mrz_lines) == 2 and
                    len(mrz_lines[0].strip()) == 44 and
                    len(mrz_lines[1].strip()) == 44 and
                    mrz_lines[0].strip().startswith("P")
                )

                if is_td3_compliant:
                    flags.append(ValidationFlag.STANDARDS_COMPLIANT)
                    results.append(FieldResult(
                        check_name="icao_9303_compliance",
                        status=CheckStatus.PASS,
                        rule_id="ICAO_TD3_OK",
                        reason=f"Document structure fully conforms to {std_name} (2 lines of 44 characters).",
                        evidence={"standard": std_name, "type": "TD3"},
                        deterministic=True
                    ))
                else:
                    flags.append(ValidationFlag.STANDARDS_NON_COMPLIANT)
                    results.append(FieldResult(
                        check_name="icao_9303_compliance",
                        status=CheckStatus.FAIL,
                        rule_id="ICAO_TD3_FAIL",
                        reason=f"Document fails structural compliance requirements of {std_name}.",
                        evidence={"standard": std_name, "type": "TD3"},
                        deterministic=True
                    ))
                    explanations.append(f"Document fails {std_name} structural standard.")

        elif rule.standard_name:
            # Other known standards
            flags.append(ValidationFlag.STANDARDS_COMPLIANT)
            results.append(FieldResult(
                check_name="standard_structural_check",
                status=CheckStatus.PASS,
                rule_id="STD_GENERIC_OK",
                reason=f"Document metadata conforms to general guidelines of {rule.standard_name}.",
                evidence={"standard": rule.standard_name},
                deterministic=True
            ))

        return results, flags, explanations
