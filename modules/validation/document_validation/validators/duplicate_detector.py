"""
Duplicate identity detector based on demographic matches.
"""
from typing import Any, Dict, List, Optional, Tuple

from document_validation.core.normalizer import NormalizedInput, normalize_document_number
from document_validation.core.privacy import mask_name, mask_date, mask_document_number
from document_validation.core.rule_registry import DocumentRule
from document_validation.database.repository import BorderSecurityRepository
from document_validation.models.flags import ValidationFlag
from document_validation.models.result_model import CheckStatus, FieldResult
from document_validation.validators.base import BaseValidator


class DuplicateIdentityDetector(BaseValidator):
    """
    Detects if an individual (Name + Date of Birth) is registered
    under multiple distinct document numbers in the system.
    """

    def __init__(self, repository: Optional[BorderSecurityRepository] = None):
        self.repository = repository

    def validate(
        self,
        norm_input: NormalizedInput,
        rule: DocumentRule,
        **kwargs
    ) -> Tuple[List[FieldResult], List[ValidationFlag], List[str]]:
        results: List[FieldResult] = []
        flags: List[ValidationFlag] = []
        explanations: List[str] = []

        if not self.repository:
            return results, flags, explanations

        name = norm_input.name
        dob_str = norm_input.dates.dob.isoformat() if norm_input.dates.dob else norm_input.original.date_of_birth
        curr_doc_num = norm_input.document_number

        if not name or not dob_str:
            return results, flags, explanations

        matched_records, err = self.repository.find_duplicate_identities(name, dob_str, curr_doc_num)

        if err:
            flags.append(ValidationFlag.DUPLICATE_LOOKUP_INCONCLUSIVE)
            results.append(FieldResult(
                check_name="duplicate_identity_check",
                status=CheckStatus.UNKNOWN,
                rule_id="DUP_ID_ERR",
                reason=f"Duplicate identity lookup inconclusive due to database communication error: {err}",
                evidence={"error": err},
                deterministic=False
            ))
            explanations.append(f"Database lookup inconclusive for duplicate identities ({err}).")
            return results, flags, explanations

        # Collect distinct document numbers from matched records and current document
        distinct_numbers = set()
        clean_curr_num = normalize_document_number(curr_doc_num)
        if clean_curr_num:
            distinct_numbers.add(clean_curr_num)

        matched_summaries: List[Dict[str, Any]] = []
        for r in matched_records:
            item_num = normalize_document_number(r["document_number"])
            distinct_numbers.add(item_num)
            matched_summaries.append({
                "masked_document_number": r["masked_document_number"],
                "document_type": r["document_type"],
                "status": r["status"]
            })

        distinct_count = len(distinct_numbers)

        if distinct_count > 1:
            flags.append(ValidationFlag.DUPLICATE_IDENTITY_FOUND)
            flags.append(ValidationFlag.MULTIPLE_DOCUMENT_NUMBERS)
            flags.append(ValidationFlag.POSSIBLE_IDENTITY_COLLISION)

            results.append(FieldResult(
                check_name="duplicate_identity_check",
                status=CheckStatus.WARN,
                rule_id="DUP_ID_FOUND",
                reason=(
                    f"Identity '{mask_name(name)}' (DOB: {mask_date(dob_str)}) is linked to "
                    f"{distinct_count} distinct document numbers in the system. "
                    "Notice: Demographic name-and-DOB matching can produce accidental collisions (homonyms); "
                    "biometric verification is required before making an identity-fraud determination."
                ),
                evidence={
                    "distinct_documents_count": distinct_count,
                    "matched_records": matched_summaries,
                    "matching_fields": ["name", "date_of_birth"]
                },
                deterministic=False
            ))
            explanations.append(
                f"Duplicate identity alert: holder details appear under {distinct_count} different document numbers. "
                "Manual/biometric review recommended."
            )

        else:
            results.append(FieldResult(
                check_name="duplicate_identity_check",
                status=CheckStatus.PASS,
                rule_id="DUP_ID_NONE",
                reason="No conflicting duplicate document registrations found for this identity.",
                evidence={"distinct_documents_count": distinct_count},
                deterministic=False
            ))

        return results, flags, explanations
