"""
Date logic and consistency validator.
"""
from datetime import date
from typing import List, Tuple, Optional

from document_validation.core.normalizer import NormalizedInput
from document_validation.core.privacy import mask_date
from document_validation.core.rule_registry import DocumentRule
from document_validation.models.flags import ValidationFlag
from document_validation.models.result_model import CheckStatus, FieldResult
from document_validation.validators.base import BaseValidator


class DateValidator(BaseValidator):
    """
    Validates calendar integrity, age realism, chronological sequence
    between DOB, Issue Date, and Expiry Date, and visa stay duration.
    """

    def validate(
        self,
        norm_input: NormalizedInput,
        rule: DocumentRule,
        validation_date: Optional[date] = None,
        **kwargs
    ) -> Tuple[List[FieldResult], List[ValidationFlag], List[str]]:
        results: List[FieldResult] = []
        flags: List[ValidationFlag] = []
        explanations: List[str] = []

        ref_date = validation_date or date.today()
        dates = norm_input.dates
        orig = norm_input.original

        # 1. Date Format Validity Check
        if orig.date_of_birth and not dates.dob_raw_valid:
            flags.append(ValidationFlag.INVALID_DATE_FORMAT)
            flags.append(ValidationFlag.INVALID_DATE_OF_BIRTH)
            results.append(FieldResult(
                check_name="dob_format_check",
                status=CheckStatus.FAIL,
                rule_id="DATE_FMT_DOB",
                reason=f"Date of birth string '{orig.date_of_birth}' could not be parsed as a valid calendar date.",
                evidence={"raw_dob": orig.date_of_birth},
                deterministic=True
            ))
            explanations.append(f"Invalid date of birth format or non-existent calendar date: '{orig.date_of_birth}'.")

        if orig.date_of_issue and not dates.issue_date_raw_valid:
            flags.append(ValidationFlag.INVALID_DATE_FORMAT)
            results.append(FieldResult(
                check_name="issue_date_format_check",
                status=CheckStatus.FAIL,
                rule_id="DATE_FMT_ISSUE",
                reason=f"Date of issue string '{orig.date_of_issue}' could not be parsed as a valid calendar date.",
                evidence={"raw_issue": orig.date_of_issue},
                deterministic=True
            ))
            explanations.append(f"Invalid date of issue format: '{orig.date_of_issue}'.")

        if orig.date_of_expiry and not dates.expiry_date_raw_valid:
            flags.append(ValidationFlag.INVALID_DATE_FORMAT)
            results.append(FieldResult(
                check_name="expiry_date_format_check",
                status=CheckStatus.FAIL,
                rule_id="DATE_FMT_EXPIRY",
                reason=f"Date of expiry string '{orig.date_of_expiry}' could not be parsed as a valid calendar date.",
                evidence={"raw_expiry": orig.date_of_expiry},
                deterministic=True
            ))
            explanations.append(f"Invalid date of expiry format: '{orig.date_of_expiry}'.")

        # 2. Date of Birth Logic Check
        if dates.dob:
            masked_dob = mask_date(dates.dob.isoformat())
            # Check DOB not future
            if dates.dob > ref_date:
                flags.append(ValidationFlag.FUTURE_DATE_OF_BIRTH)
                flags.append(ValidationFlag.INVALID_DATE_LOGIC)
                results.append(FieldResult(
                    check_name="dob_future_check",
                    status=CheckStatus.FAIL,
                    rule_id="DATE_LOGIC_DOB_01",
                    reason=f"Date of birth ({masked_dob}) is in the future relative to validation date ({ref_date.isoformat()}).",
                    evidence={"dob_year": dates.dob.year, "validation_year": ref_date.year},
                    deterministic=True
                ))
                explanations.append(f"Date of birth cannot be in the future (DOB: {masked_dob}).")
            else:
                # Age calculation
                age_years = ref_date.year - dates.dob.year - ((ref_date.month, ref_date.day) < (dates.dob.month, dates.dob.day))
                if age_years > 130:
                    flags.append(ValidationFlag.UNREALISTIC_AGE)
                    flags.append(ValidationFlag.INVALID_DATE_LOGIC)
                    results.append(FieldResult(
                        check_name="dob_age_realism_check",
                        status=CheckStatus.FAIL,
                        rule_id="DATE_LOGIC_AGE_01",
                        reason=f"Calculated age ({age_years} years) exceeds realistic human lifespan threshold (130 years).",
                        evidence={"calculated_age": age_years},
                        deterministic=True
                    ))
                    explanations.append(f"Date of birth produces unrealistic age ({age_years} years).")
                else:
                    results.append(FieldResult(
                        check_name="dob_logic_check",
                        status=CheckStatus.PASS,
                        rule_id="DATE_LOGIC_DOB_OK",
                        reason=f"Date of birth is chronologically valid and represents realistic age ({age_years} years).",
                        evidence={"age_years": age_years},
                        deterministic=True
                    ))

        # 3. Issue Date Logic Check
        if dates.issue_date:
            masked_issue = mask_date(dates.issue_date.isoformat())
            if dates.issue_date > ref_date:
                flags.append(ValidationFlag.FUTURE_ISSUE_DATE)
                flags.append(ValidationFlag.INVALID_DATE_LOGIC)
                results.append(FieldResult(
                    check_name="issue_date_future_check",
                    status=CheckStatus.FAIL,
                    rule_id="DATE_LOGIC_ISSUE_01",
                    reason=f"Document issue date ({masked_issue}) is in the future relative to validation date ({ref_date.isoformat()}).",
                    evidence={"issue_date": masked_issue},
                    deterministic=True
                ))
                explanations.append(f"Document date of issue cannot be in the future ({masked_issue}).")
            else:
                results.append(FieldResult(
                    check_name="issue_date_future_check",
                    status=CheckStatus.PASS,
                    rule_id="DATE_LOGIC_ISSUE_OK",
                    reason="Document issue date is not in the future.",
                    evidence={"issue_date": masked_issue},
                    deterministic=True
                ))

            # DOB vs Issue Date
            if dates.dob and dates.issue_date < dates.dob:
                flags.append(ValidationFlag.INVALID_DATE_LOGIC)
                results.append(FieldResult(
                    check_name="issue_after_dob_check",
                    status=CheckStatus.FAIL,
                    rule_id="DATE_LOGIC_ISSUE_DOB",
                    reason="Document issue date precedes the holder's date of birth.",
                    evidence={},
                    deterministic=True
                ))
                explanations.append("Document issue date cannot precede holder's date of birth.")

        # 4. Issue Date vs Expiry Date Sequence Check
        if dates.issue_date and dates.expiry_date:
            if dates.expiry_date <= dates.issue_date:
                flags.append(ValidationFlag.EXPIRY_BEFORE_ISSUE)
                flags.append(ValidationFlag.INVALID_DATE_LOGIC)
                results.append(FieldResult(
                    check_name="expiry_after_issue_check",
                    status=CheckStatus.FAIL,
                    rule_id="DATE_LOGIC_SEQ_01",
                    reason=(
                        f"Expiry date ({dates.expiry_date.isoformat()}) is equal to or earlier than "
                        f"issue date ({dates.issue_date.isoformat()})."
                    ),
                    evidence={"issue_date": str(dates.issue_date), "expiry_date": str(dates.expiry_date)},
                    deterministic=True
                ))
                explanations.append("Document expiry date must be strictly after the date of issue.")
            else:
                results.append(FieldResult(
                    check_name="expiry_after_issue_check",
                    status=CheckStatus.PASS,
                    rule_id="DATE_LOGIC_SEQ_OK",
                    reason="Expiry date is chronologically after issue date.",
                    evidence={},
                    deterministic=True
                ))

        # 5. Visa-Specific Validity & Stay Duration Check
        if norm_input.document_type == "visa" and dates.issue_date and dates.expiry_date:
            total_validity_days = (dates.expiry_date - dates.issue_date).days
            if norm_input.stay_days is not None:
                if norm_input.stay_days > total_validity_days:
                    flags.append(ValidationFlag.INVALID_STAY_DURATION)
                    flags.append(ValidationFlag.INVALID_VISA_VALIDITY)
                    results.append(FieldResult(
                        check_name="visa_stay_duration_check",
                        status=CheckStatus.FAIL,
                        rule_id="VISA_STAY_01",
                        reason=(
                            f"Declared stay duration ({norm_input.stay_days} days) exceeds total "
                            f"visa validity window ({total_validity_days} days)."
                        ),
                        evidence={"stay_days": norm_input.stay_days, "validity_window_days": total_validity_days},
                        deterministic=True
                    ))
                    explanations.append(
                        f"Visa stay duration ({norm_input.stay_days} days) exceeds validity window ({total_validity_days} days)."
                    )
                else:
                    results.append(FieldResult(
                        check_name="visa_stay_duration_check",
                        status=CheckStatus.PASS,
                        rule_id="VISA_STAY_OK",
                        reason="Visa stay duration is within total validity window.",
                        evidence={"stay_days": norm_input.stay_days, "validity_window_days": total_validity_days},
                        deterministic=True
                    ))

        return results, flags, explanations
