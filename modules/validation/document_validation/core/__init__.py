"""
Core utilities and services package.
"""
from document_validation.core.normalizer import (
    NormalizedInput,
    NormalizedDates,
    normalize_input_data,
    normalize_document_number,
    normalize_string,
    parse_date_safe,
    parse_stay_duration,
)
from document_validation.core.privacy import (
    mask_document_number,
    mask_name,
    mask_date,
    generate_identity_token,
    sanitize_dict_for_logging,
)
from document_validation.core.rule_registry import (
    DocumentRule,
    RuleRegistry,
)

__all__ = [
    "NormalizedInput",
    "NormalizedDates",
    "normalize_input_data",
    "normalize_document_number",
    "normalize_string",
    "parse_date_safe",
    "parse_stay_duration",
    "mask_document_number",
    "mask_name",
    "mask_date",
    "generate_identity_token",
    "sanitize_dict_for_logging",
    "DocumentRule",
    "RuleRegistry",
]
