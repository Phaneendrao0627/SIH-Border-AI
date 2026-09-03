"""
Module 2: Document Validation Engine.
AI-Based Fake Identity & Document Screening System (SIH26188).
"""
from document_validation.config import ValidationConfig
from document_validation.engine import DocumentValidationEngine
from document_validation.models.flags import ValidationFlag
from document_validation.models.input_contract import ValidationInput, validate_and_parse_input
from document_validation.models.result_model import (
    CheckStatus,
    DatabaseResult,
    FieldResult,
    ValidationReport,
    ValidationStatus,
)
from document_validation.core.rule_registry import DocumentRule, RuleRegistry
from document_validation.database.repository import BorderSecurityRepository
from document_validation.database.seeder import seed_mock_database

__version__ = "2.0.0"

__all__ = [
    "DocumentValidationEngine",
    "ValidationConfig",
    "ValidationFlag",
    "ValidationInput",
    "validate_and_parse_input",
    "ValidationReport",
    "ValidationStatus",
    "CheckStatus",
    "FieldResult",
    "DatabaseResult",
    "DocumentRule",
    "RuleRegistry",
    "BorderSecurityRepository",
    "seed_mock_database",
]
