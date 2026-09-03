"""
Output contract models and serialization for Module 2: Document Validation.
"""
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, List, Optional


class ValidationStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARN = "WARN"
    INCOMPLETE = "INCOMPLETE"


class CheckStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARN = "WARN"
    UNKNOWN = "UNKNOWN"


@dataclass
class FieldResult:
    check_name: str
    status: CheckStatus
    rule_id: str
    reason: str
    evidence: Optional[Dict[str, Any]] = None
    deterministic: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "check_name": self.check_name,
            "status": self.status.value,
            "rule_id": self.rule_id,
            "reason": self.reason,
            "evidence": self.evidence or {},
            "deterministic": self.deterministic
        }


@dataclass
class DatabaseResult:
    blacklist_checked: bool = False
    blacklist_hit: bool = False
    blacklist_details: Optional[Dict[str, Any]] = None
    watchlist_checked: bool = False
    watchlist_hit: bool = False
    watchlist_details: Optional[Dict[str, Any]] = None
    duplicate_checked: bool = False
    duplicate_found: bool = False
    duplicate_count: int = 0
    duplicate_details: Optional[Dict[str, Any]] = None
    disclaimer: str = (
        "Clean local mock database lookup does NOT verify official authenticity. "
        "Intended for decision support only."
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "blacklist_checked": self.blacklist_checked,
            "blacklist_hit": self.blacklist_hit,
            "blacklist_details": self.blacklist_details,
            "watchlist_checked": self.watchlist_checked,
            "watchlist_hit": self.watchlist_hit,
            "watchlist_details": self.watchlist_details,
            "duplicate_checked": self.duplicate_checked,
            "duplicate_found": self.duplicate_found,
            "duplicate_count": self.duplicate_count,
            "duplicate_details": self.duplicate_details,
            "disclaimer": self.disclaimer
        }


@dataclass
class ValidationReport:
    request_id: str
    document_type: str
    document_number: str  # Masked identifier for privacy
    validation_timestamp: str
    validation_date: str
    overall_status: ValidationStatus
    overall_confidence: float
    validation_results: Dict[str, Any]
    flags: List[str]
    explanations: List[str]
    field_results: List[FieldResult] = field(default_factory=list)
    database_results: Optional[DatabaseResult] = None
    standards_checked: List[str] = field(default_factory=list)
    validator_version: str = "2.0.0"
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "document_type": self.document_type,
            "document_number": self.document_number,
            "validation_timestamp": self.validation_timestamp,
            "validation_date": self.validation_date,
            "overall_status": self.overall_status.value,
            "overall_confidence": round(self.overall_confidence, 2),
            "validation_results": self.validation_results,
            "flags": self.flags,
            "explanations": self.explanations,
            "field_results": [fr.to_dict() for fr in self.field_results],
            "database_results": self.database_results.to_dict() if self.database_results else None,
            "standards_checked": self.standards_checked,
            "validator_version": self.validator_version,
            "warnings": self.warnings,
            "errors": self.errors
        }
