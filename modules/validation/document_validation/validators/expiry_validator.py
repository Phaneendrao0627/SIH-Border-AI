"""
Expiry and validity status validator.
"""
from datetime import date
from typing import List, Optional, Tuple

from document_validation.core.normalizer import NormalizedInput
from document_validation.core.rule_registry import DocumentRule
from document_validation.models.flags import ValidationFlag
from document_validation.models.result_model import CheckStatus, FieldResult
from document_validation.validators.base import BaseValidator


class ExpiryValidator(BaseValidator):
    """
    Validates document expiry status relative to a specific validation date,
    calculates days remaining, and flags expired or soon-to-expire documents.
    """

    def __init__(self, expiring_soon_threshold_days: int = 180):
        self.expiring_soon_threshold_days = expiring_soon_threshold_days

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
        expiry = norm_input.dates.expiry_date

        if not expiry:
            if "date_of_expiry" in rule.mandatory_fields:
                flags.append(ValidationFlag.EXPIRY_UNKNOWN)
                flags.append(ValidationFlag.INCOMPLETE_DATA)
                results.append(FieldResult(
                    check_name="expiry_validity_check",
                    status=CheckStatus.UNKNOWN,
                    rule_id="EXP_VAL_UNKNOWN",
                    reason="Expiry date is missing or unparseable; validity status cannot be established.",
                    evidence={"validation_date": ref_date.isoformat()},
                    deterministic=True
                ))
                explanations.append("Document validity undetermined: missing expiry date.")
            return results, flags, explanations

        days_remaining = (expiry - ref_date).days

        if days_remaining < 0:
            # Document is expired
            flags.append(ValidationFlag.EXPIRED_DOCUMENT)
            results.append(FieldResult(
                check_name="expiry_validity_check",
                status=CheckStatus.FAIL,
                rule_id="EXP_VAL_EXPIRED",
                reason=(
                    f"Document expired on {expiry.isoformat()} ({abs(days_remaining)} days ago "
                    f"as of validation date {ref_date.isoformat()})."
                ),
                evidence={
                    "expiry_date": expiry.isoformat(),
                    "validation_date": ref_date.isoformat(),
                    "days_remaining": days_remaining,
                    "status": "EXPIRED"
                },
                deterministic=True
            ))
            explanations.append(
                f"Document is expired: passed expiry date by {abs(days_remaining)} days ({expiry.isoformat()})."
            )

        elif days_remaining <= self.expiring_soon_threshold_days:
            # Document is expiring soon
            flags.append(ValidationFlag.EXPIRING_SOON)
            results.append(FieldResult(
                check_name="expiry_validity_check",
                status=CheckStatus.WARN,
                rule_id="EXP_VAL_SOON",
                reason=(
                    f"Document expires within {days_remaining} days ({expiry.isoformat()}). "
                    f"Under minimum travel validity threshold ({self.expiring_soon_threshold_days} days)."
                ),
                evidence={
                    "expiry_date": expiry.isoformat(),
                    "validation_date": ref_date.isoformat(),
                    "days_remaining": days_remaining,
                    "status": "EXPIRING_SOON"
                },
                deterministic=True
            ))
            explanations.append(
                f"Document expiring soon: {days_remaining} days remaining until {expiry.isoformat()}."
            )

        else:
            # Document is currently valid
            results.append(FieldResult(
                check_name="expiry_validity_check",
                status=CheckStatus.PASS,
                rule_id="EXP_VAL_OK",
                reason=(
                    f"Document is currently valid. {days_remaining} days remaining "
                    f"until expiry ({expiry.isoformat()})."
                ),
                evidence={
                    "expiry_date": expiry.isoformat(),
                    "validation_date": ref_date.isoformat(),
                    "days_remaining": days_remaining,
                    "status": "VALID"
                },
                deterministic=True
            ))

        return results, flags, explanations
