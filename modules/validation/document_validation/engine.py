"""
Core Document Validation Engine.
Orchestrates independent validators, database lookups, and deterministic result aggregation.
"""
from datetime import date, datetime
import os
from typing import Any, Dict, List, Optional, Union

from document_validation.config import ValidationConfig
from document_validation.core.normalizer import (
    NormalizedInput,
    normalize_input_data,
    parse_date_safe,
)
from document_validation.core.privacy import mask_document_number
from document_validation.core.rule_registry import DocumentRule, RuleRegistry
from document_validation.database.repository import BorderSecurityRepository
from document_validation.models.flags import ValidationFlag
from document_validation.models.input_contract import ValidationInput, validate_and_parse_input
from document_validation.models.result_model import (
    CheckStatus,
    DatabaseResult,
    FieldResult,
    ValidationReport,
    ValidationStatus,
)
from document_validation.validators.date_validator import DateValidator
from document_validation.validators.duplicate_detector import DuplicateIdentityDetector
from document_validation.validators.expiry_validator import ExpiryValidator
from document_validation.validators.format_validator import FormatValidator
from document_validation.validators.mrz_validator import MRZValidator
from document_validation.validators.standards_validator import StandardsValidator


class DocumentValidationEngine:
    """
    Production-grade, rule-based document validation engine.
    Completely decoupled from web frameworks, OCR models, and face biometrics.
    """

    def __init__(
        self,
        config: Optional[ValidationConfig] = None,
        rule_registry: Optional[RuleRegistry] = None,
        repository: Optional[BorderSecurityRepository] = None,
    ):
        self.config = config or ValidationConfig()
        self.rule_registry = rule_registry or RuleRegistry()

        if repository:
            self.repository = repository
        elif self.config.enable_database_checks and os.path.exists(self.config.db_path):
            self.repository = BorderSecurityRepository(
                self.config.db_path, timeout=self.config.db_timeout
            )
        else:
            self.repository = None

        # Instantiate modular validators
        self.format_validator = FormatValidator()
        self.date_validator = DateValidator()
        self.expiry_validator = ExpiryValidator(
            expiring_soon_threshold_days=self.config.expiring_soon_threshold_days
        )
        self.mrz_validator = MRZValidator()
        self.standards_validator = StandardsValidator()
        self.duplicate_detector = DuplicateIdentityDetector(self.repository)

    def validate(
        self,
        raw_payload: Any,
        validation_date: Optional[Union[date, str]] = None,
    ) -> ValidationReport:
        """
        Validates structured document data against schema, country format rules,
        date logic, MRZ checksums, and local mock border databases.
        """
        start_time = datetime.now()

        # 1. Resolve validation date
        ref_date = date.today()
        if validation_date:
            if isinstance(validation_date, str):
                parsed_d, ok = parse_date_safe(validation_date)
                if ok and parsed_d:
                    ref_date = parsed_d
            elif isinstance(validation_date, date):
                ref_date = validation_date
        elif self.config.validation_date:
            ref_date = self.config.validation_date

        ref_date_str = ref_date.isoformat()

        # 2. Schema and Input Validation
        parsed_input, schema_errors, schema_flags = validate_and_parse_input(raw_payload)

        if schema_errors or not parsed_input:
            # Handle malformed / missing payload safely
            masked_id = "[UNAVAILABLE]"
            if isinstance(raw_payload, dict):
                for k in ["document_number", "passport_number", "visa_number", "national_id_number"]:
                    if k in raw_payload and isinstance(raw_payload[k], str):
                        masked_id = mask_document_number(raw_payload[k])
                        break

            return ValidationReport(
                request_id=raw_payload.get("request_id", "UNKNOWN") if isinstance(raw_payload, dict) else "UNKNOWN",
                document_type=raw_payload.get("document_type", "UNKNOWN") if isinstance(raw_payload, dict) else "UNKNOWN",
                document_number=masked_id,
                validation_timestamp=start_time.isoformat(),
                validation_date=ref_date_str,
                overall_status=ValidationStatus.INCOMPLETE,
                overall_confidence=0.0,
                validation_results={
                    "format_valid": False,
                    "date_logic_valid": False,
                    "not_expired": False,
                    "mrz_checksum_valid": None,
                    "on_blacklist": False,
                    "duplicate_identity_found": False,
                    "standards_compliant": False,
                },
                flags=[f.value for f in schema_flags],
                explanations=[f"Input contract violation: {err}" for err in schema_errors],
                field_results=[
                    FieldResult(
                        check_name="input_schema_validation",
                        status=CheckStatus.FAIL,
                        rule_id="SCHEMA_CONTRACT_01",
                        reason=err,
                        evidence={},
                        deterministic=True,
                    )
                    for err in schema_errors
                ],
                database_results=None,
                standards_checked=[],
                validator_version=self.config.validator_version,
                warnings=[],
                errors=schema_errors,
            )

        # 3. Normalization
        norm_input = normalize_input_data(parsed_input)
        masked_doc_num = mask_document_number(norm_input.document_number)

        # 4. Rule Resolution
        rule, is_fallback = self.rule_registry.get_rule(
            norm_input.document_type, norm_input.country_code
        )

        all_field_results: List[FieldResult] = []
        all_flags: List[ValidationFlag] = []
        all_explanations: List[str] = []
        warnings: List[str] = []
        errors: List[str] = []
        standards_checked: List[str] = []

        if rule.standard_name:
            standards_checked.append(rule.standard_name)

        if is_fallback:
            all_flags.append(ValidationFlag.UNSUPPORTED_STANDARD)
            all_flags.append(ValidationFlag.LOW_CONFIDENCE_STANDARD)
            warnings.append(
                f"Country-specific rule for '{norm_input.country_code}' not found; "
                f"applied generic rule '{rule.rule_id}'."
            )

        # 5. Format & Mandatory Field Validator
        fmt_res, fmt_flags, fmt_exp = self.format_validator.validate(norm_input, rule)
        all_field_results.extend(fmt_res)
        all_flags.extend(fmt_flags)
        all_explanations.extend(fmt_exp)

        # 6. Date Logic Validator
        dt_res, dt_flags, dt_exp = self.date_validator.validate(
            norm_input, rule, validation_date=ref_date
        )
        all_field_results.extend(dt_res)
        all_flags.extend(dt_flags)
        all_explanations.extend(dt_exp)

        # 7. Expiry Validator
        exp_res, exp_flags, exp_exp = self.expiry_validator.validate(
            norm_input, rule, validation_date=ref_date
        )
        all_field_results.extend(exp_res)
        all_flags.extend(exp_flags)
        all_explanations.extend(exp_exp)

        # 8. MRZ Validator (Passports and MRZ documents)
        mrz_res, mrz_flags, mrz_exp = self.mrz_validator.validate(norm_input, rule)
        all_field_results.extend(mrz_res)
        all_flags.extend(mrz_flags)
        all_explanations.extend(mrz_exp)

        # 9. Standards Compliance Validator
        std_res, std_flags, std_exp = self.standards_validator.validate(norm_input, rule)
        all_field_results.extend(std_res)
        all_flags.extend(std_flags)
        all_explanations.extend(std_exp)

        # 10. Database Lookups (Blacklist, Watchlist, Duplicates)
        db_summary = DatabaseResult()
        on_blacklist = False
        duplicate_found = False

        if self.config.enable_database_checks and self.repository:
            # 10.1 Blacklist Check
            db_summary.blacklist_checked = True
            bl_result = self.repository.check_blacklist(norm_input.document_number)
            if bl_result.error:
                all_flags.append(ValidationFlag.WATCHLIST_DATABASE_UNAVAILABLE)
                all_flags.append(ValidationFlag.WATCHLIST_LOOKUP_INCONCLUSIVE)
                warnings.append(bl_result.error)
                all_field_results.append(FieldResult(
                    check_name="blacklist_check",
                    status=CheckStatus.UNKNOWN,
                    rule_id="DB_BL_ERR",
                    reason=f"Blacklist check could not be completed: {bl_result.error}",
                    evidence={},
                    deterministic=False,
                ))
            elif bl_result.hit:
                on_blacklist = True
                db_summary.blacklist_hit = True
                db_summary.blacklist_details = bl_result.record
                all_flags.append(ValidationFlag.DOCUMENT_ON_BLACKLIST)
                all_flags.append(ValidationFlag.BLACKLIST_MATCH)
                reason_str = bl_result.record.get("reason", "Flagged on border blacklist")
                all_field_results.append(FieldResult(
                    check_name="blacklist_check",
                    status=CheckStatus.FAIL,
                    rule_id="DB_BL_MATCH",
                    reason=f"CRITICAL: Document number matches border security blacklist ({reason_str}).",
                    evidence={
                        "masked_document_number": masked_doc_num,
                        "source": bl_result.record.get("source_label"),
                        "reason": reason_str,
                    },
                    deterministic=False,
                ))
                all_explanations.append(f"Security Alert: Document {masked_doc_num} is listed on blacklist ({reason_str}).")
            else:
                all_field_results.append(FieldResult(
                    check_name="blacklist_check",
                    status=CheckStatus.PASS,
                    rule_id="DB_BL_CLEAR",
                    reason="Document number not present on local mock border security blacklist.",
                    evidence={"masked_document_number": masked_doc_num},
                    deterministic=False,
                ))

            # 10.2 Watchlist Check (Name + DOB)
            dob_iso = norm_input.dates.dob.isoformat() if norm_input.dates.dob else norm_input.original.date_of_birth
            if norm_input.name and dob_iso:
                db_summary.watchlist_checked = True
                wl_result = self.repository.check_watchlist(norm_input.name, dob_iso)
                if wl_result.error:
                    all_flags.append(ValidationFlag.WATCHLIST_LOOKUP_INCONCLUSIVE)
                    warnings.append(wl_result.error)
                elif wl_result.hit:
                    db_summary.watchlist_hit = True
                    db_summary.watchlist_details = wl_result.record
                    all_flags.append(ValidationFlag.IDENTITY_ON_WATCHLIST)
                    wl_reason = wl_result.record.get("reason", "Watchlist match")
                    all_field_results.append(FieldResult(
                        check_name="watchlist_check",
                        status=CheckStatus.FAIL,
                        rule_id="DB_WL_MATCH",
                        reason=f"CRITICAL: Identity matches border security watchlist ({wl_reason}).",
                        evidence={
                            "source": wl_result.record.get("source_label"),
                            "reason": wl_reason,
                        },
                        deterministic=False,
                    ))
                    all_explanations.append(f"Security Alert: Person identity is listed on watchlist ({wl_reason}).")
                else:
                    all_field_results.append(FieldResult(
                        check_name="watchlist_check",
                        status=CheckStatus.PASS,
                        rule_id="DB_WL_CLEAR",
                        reason="Identity (Name + DOB) not found on watchlist database.",
                        evidence={},
                        deterministic=False,
                    ))

            # 10.3 Duplicate Identity Detector
            db_summary.duplicate_checked = True
            dup_res, dup_flags, dup_exp = self.duplicate_detector.validate(norm_input, rule)
            all_field_results.extend(dup_res)
            all_flags.extend(dup_flags)
            all_explanations.extend(dup_exp)
            if ValidationFlag.DUPLICATE_IDENTITY_FOUND in dup_flags:
                duplicate_found = True
                db_summary.duplicate_found = True
                for res in dup_res:
                    if res.check_name == "duplicate_identity_check" and res.evidence:
                        db_summary.duplicate_count = res.evidence.get("distinct_documents_count", 0)
                        db_summary.duplicate_details = res.evidence

        # 11. Summarize Check Results
        # Check overall format validity
        format_checks = [r for r in all_field_results if r.check_name in ["format_pattern_check", "document_length_check", "character_set_check", "placeholder_check"]]
        format_valid = all(r.status == CheckStatus.PASS for r in format_checks) if format_checks else False

        # Check date logic validity
        date_checks = [r for r in all_field_results if r.check_name in ["dob_logic_check", "dob_future_check", "issue_date_future_check", "expiry_after_issue_check", "visa_stay_duration_check"]]
        date_logic_valid = not any(r.status == CheckStatus.FAIL for r in date_checks)

        # Check not expired
        exp_checks = [r for r in all_field_results if r.check_name == "expiry_validity_check"]
        not_expired = all(r.status != CheckStatus.FAIL for r in exp_checks) if exp_checks else False

        # MRZ checksum validity
        mrz_ck_checks = [r for r in all_field_results if "checksum" in r.check_name or "mrz_structure" in r.check_name]
        mrz_checksum_valid = None
        if mrz_ck_checks:
            mrz_checksum_valid = all(r.status == CheckStatus.PASS for r in mrz_ck_checks)

        # Standards compliance
        std_checks = [r for r in all_field_results if "compliance" in r.check_name or "structural" in r.check_name]
        standards_compliant = None
        if std_checks:
            standards_compliant = all(r.status == CheckStatus.PASS for r in std_checks)

        validation_results_summary = {
            "format_valid": format_valid,
            "date_logic_valid": date_logic_valid,
            "not_expired": not_expired,
            "mrz_checksum_valid": mrz_checksum_valid,
            "on_blacklist": on_blacklist,
            "duplicate_identity_found": duplicate_found,
            "standards_compliant": standards_compliant,
        }

        # 12. Deterministic Status Aggregation
        # Critical failure conditions:
        critical_fail_flags = {
            ValidationFlag.DOCUMENT_ON_BLACKLIST,
            ValidationFlag.IDENTITY_ON_WATCHLIST,
            ValidationFlag.EXPIRED_DOCUMENT,
            ValidationFlag.MRZ_CHECKSUM_INVALID,
            ValidationFlag.MRZ_COMPOSITE_CHECKSUM_INVALID,
            ValidationFlag.MRZ_DOCUMENT_NUMBER_MISMATCH,
            ValidationFlag.MRZ_DATE_OF_BIRTH_MISMATCH,
            ValidationFlag.MRZ_EXPIRY_DATE_MISMATCH,
            ValidationFlag.MRZ_STRUCTURE_INVALID,
            ValidationFlag.FUTURE_DATE_OF_BIRTH,
            ValidationFlag.FUTURE_ISSUE_DATE,
            ValidationFlag.EXPIRY_BEFORE_ISSUE,
            ValidationFlag.UNREALISTIC_AGE,
            ValidationFlag.INVALID_DATE_FORMAT,
            ValidationFlag.INVALID_DATE_OF_BIRTH,
            ValidationFlag.INVALID_DOCUMENT_NUMBER_FORMAT,
            ValidationFlag.INVALID_DOCUMENT_NUMBER_LENGTH,
            ValidationFlag.INVALID_DOCUMENT_NUMBER_CHARACTERS,
            ValidationFlag.COUNTRY_FORMAT_MISMATCH,
            ValidationFlag.SUSPICIOUS_PLACEHOLDER_NUMBER,
            ValidationFlag.INVALID_STAY_DURATION,
        }

        has_critical_failure = any(f in critical_fail_flags for f in all_flags)
        is_incomplete = (
            ValidationFlag.INCOMPLETE_DATA in all_flags or
            ValidationFlag.MISSING_DOCUMENT_NUMBER in all_flags or
            ValidationFlag.MISSING_NAME in all_flags or
            ValidationFlag.MISSING_DATE_OF_BIRTH in all_flags or
            ValidationFlag.MISSING_EXPIRY_DATE in all_flags or
            (rule.requires_mrz and ValidationFlag.MRZ_UNAVAILABLE in all_flags)
        )

        warning_flags = {
            ValidationFlag.EXPIRING_SOON,
            ValidationFlag.DUPLICATE_IDENTITY_FOUND,
            ValidationFlag.MULTIPLE_DOCUMENT_NUMBERS,
            ValidationFlag.LOW_MRZ_CONFIDENCE,
            ValidationFlag.LOW_OCR_CONFIDENCE,
            ValidationFlag.UNSUPPORTED_STANDARD,
            ValidationFlag.LOW_CONFIDENCE_STANDARD,
            ValidationFlag.WATCHLIST_DATABASE_UNAVAILABLE,
            ValidationFlag.WATCHLIST_LOOKUP_INCONCLUSIVE,
        }
        has_warnings = any(f in warning_flags for f in all_flags)

        if has_critical_failure:
            overall_status = ValidationStatus.FAIL
        elif is_incomplete:
            overall_status = ValidationStatus.INCOMPLETE
        elif has_warnings:
            overall_status = ValidationStatus.WARN
        else:
            overall_status = ValidationStatus.PASS

        # 13. Calculate Confidence
        base_confidence = 1.0
        if is_fallback:
            base_confidence -= 0.15
        if ValidationFlag.LOW_OCR_CONFIDENCE in all_flags:
            base_confidence -= 0.20
        if ValidationFlag.LOW_MRZ_CONFIDENCE in all_flags:
            base_confidence -= 0.15
        if ValidationFlag.WATCHLIST_LOOKUP_INCONCLUSIVE in all_flags:
            base_confidence -= 0.10
        if is_incomplete:
            base_confidence -= 0.40
        overall_confidence = max(0.20, min(1.0, base_confidence))

        # Distinct flags list
        flag_strings = list(dict.fromkeys(f.value for f in all_flags))

        # Default explanation if none raised
        if not all_explanations and overall_status == ValidationStatus.PASS:
            all_explanations.append("All structural, date logic, checksum, and blacklist checks passed successfully.")

        report = ValidationReport(
            request_id=parsed_input.request_id,
            document_type=parsed_input.document_type,
            document_number=masked_doc_num,
            validation_timestamp=start_time.isoformat(),
            validation_date=ref_date_str,
            overall_status=overall_status,
            overall_confidence=overall_confidence,
            validation_results=validation_results_summary,
            flags=flag_strings,
            explanations=all_explanations,
            field_results=all_field_results,
            database_results=db_summary,
            standards_checked=standards_checked,
            validator_version=self.config.validator_version,
            warnings=warnings,
            errors=errors,
        )

        return report
