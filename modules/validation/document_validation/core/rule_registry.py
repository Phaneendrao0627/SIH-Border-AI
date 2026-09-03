"""
Configurable Document Type and Country Rule Registry.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import re


@dataclass
class DocumentRule:
    rule_id: str
    document_type: str
    country_code: Optional[str]  # None indicates generic fallback for doc_type
    doc_number_pattern: str
    min_length: int
    max_length: int
    allowed_characters_desc: str
    mandatory_fields: List[str]
    optional_fields: List[str] = field(default_factory=list)
    requires_mrz: bool = False
    standard_name: Optional[str] = None
    is_generic_fallback: bool = False
    description: str = ""

    def validate_pattern(self, doc_number: str) -> bool:
        """Validates doc_number string against regex pattern."""
        if not doc_number:
            return False
        return bool(re.match(self.doc_number_pattern, doc_number))

    def validate_length(self, doc_number: str) -> bool:
        """Validates doc_number length."""
        if not doc_number:
            return False
        return self.min_length <= len(doc_number) <= self.max_length


class RuleRegistry:
    """
    Registry for country-specific and generic document rules.
    Allows runtime configuration of new countries without code modifications.
    """
    def __init__(self):
        self._rules: Dict[Tuple[str, Optional[str]], DocumentRule] = {}
        self._generic_rules: Dict[str, DocumentRule] = {}
        self._initialize_default_rules()

    def register_rule(self, rule: DocumentRule) -> None:
        """Registers a document validation rule."""
        key = (rule.document_type.lower(), rule.country_code.upper() if rule.country_code else None)
        self._rules[key] = rule
        if rule.country_code is None or rule.is_generic_fallback:
            self._generic_rules[rule.document_type.lower()] = rule

    def get_rule(self, document_type: str, country_code: Optional[str]) -> Tuple[Optional[DocumentRule], bool]:
        """
        Retrieves the most specific rule available.
        Returns: (DocumentRule, is_fallback)
        """
        clean_type = document_type.strip().lower() if document_type else "unknown"
        clean_country = country_code.strip().upper() if country_code else None

        # 1. Exact match (doc_type, country)
        if clean_country:
            key = (clean_type, clean_country)
            if key in self._rules:
                return self._rules[key], False

        # 2. Generic document type fallback
        if clean_type in self._generic_rules:
            return self._generic_rules[clean_type], True

        # 3. Ultimate safe fallback for unknown document types
        ultimate_fallback = DocumentRule(
            rule_id="RULE_GENERIC_UNKNOWN_DOC",
            document_type=clean_type,
            country_code=None,
            doc_number_pattern=r"^[A-Za-z0-9\-_]{4,30}$",
            min_length=4,
            max_length=30,
            allowed_characters_desc="Alphanumeric, hyphens, and underscores (4-30 chars)",
            mandatory_fields=["document_number", "name"],
            optional_fields=["date_of_birth", "country_code", "date_of_expiry"],
            requires_mrz=False,
            standard_name=None,
            is_generic_fallback=True,
            description="Safe fallback rule for unclassified or unknown document types."
        )
        return ultimate_fallback, True

    def _initialize_default_rules(self) -> None:
        # 1. India Passport (IND)
        # Standard Indian Passport: 1 uppercase letter followed by 7 digits (Total 8 characters)
        self.register_rule(DocumentRule(
            rule_id="RULE_PASSPORT_IND",
            document_type="passport",
            country_code="IND",
            doc_number_pattern=r"^[A-Z][0-9]{7}$",
            min_length=8,
            max_length=8,
            allowed_characters_desc="One uppercase letter followed by exactly 7 numeric digits",
            mandatory_fields=["document_number", "name", "date_of_birth", "country_code", "date_of_expiry"],
            optional_fields=["date_of_issue", "gender", "mrz"],
            requires_mrz=True,
            standard_name="ICAO Doc 9303 Part 4 (TD3)",
            is_generic_fallback=False,
            description="Official Indian Passport specification under ICAO Doc 9303 standard."
        ))

        # 2. United States Passport (USA)
        self.register_rule(DocumentRule(
            rule_id="RULE_PASSPORT_USA",
            document_type="passport",
            country_code="USA",
            doc_number_pattern=r"^[0-9]{9}$|^[C][0-9]{8}$",
            min_length=9,
            max_length=9,
            allowed_characters_desc="9 numeric digits or 'C' followed by 8 digits (Passport Card)",
            mandatory_fields=["document_number", "name", "date_of_birth", "country_code", "date_of_expiry"],
            optional_fields=["date_of_issue", "gender", "mrz"],
            requires_mrz=True,
            standard_name="ICAO Doc 9303 Part 4 (TD3)",
            is_generic_fallback=False,
            description="United States Passport format under ICAO Doc 9303."
        ))

        # 3. Generic Passports
        self.register_rule(DocumentRule(
            rule_id="RULE_PASSPORT_GENERIC",
            document_type="passport",
            country_code=None,
            doc_number_pattern=r"^[A-Z0-9]{6,12}$",
            min_length=6,
            max_length=12,
            allowed_characters_desc="6 to 12 alphanumeric uppercase characters",
            mandatory_fields=["document_number", "name", "date_of_birth", "date_of_expiry"],
            optional_fields=["country_code", "date_of_issue", "gender", "mrz"],
            requires_mrz=True,
            standard_name="ICAO Doc 9303 (Generic TD3)",
            is_generic_fallback=True,
            description="Generic fallback rule for international passports."
        ))

        # 4. Generic Visas
        self.register_rule(DocumentRule(
            rule_id="RULE_VISA_GENERIC",
            document_type="visa",
            country_code=None,
            doc_number_pattern=r"^[A-Z0-9]{6,15}$",
            min_length=6,
            max_length=15,
            allowed_characters_desc="6 to 15 alphanumeric characters",
            mandatory_fields=["document_number", "name", "date_of_birth", "date_of_issue", "date_of_expiry"],
            optional_fields=["country_code", "visa_type", "stay_duration", "entry_validity"],
            requires_mrz=False,
            standard_name="ICAO Doc 9303 Part 7 (MRV)",
            is_generic_fallback=True,
            description="Generic fallback rule for visa documents."
        ))

        # 5. Generic National Identity Documents
        self.register_rule(DocumentRule(
            rule_id="RULE_NATIONAL_ID_GENERIC",
            document_type="national_id",
            country_code=None,
            doc_number_pattern=r"^[A-Z0-9]{6,20}$",
            min_length=6,
            max_length=20,
            allowed_characters_desc="6 to 20 alphanumeric characters",
            mandatory_fields=["document_number", "name", "date_of_birth"],
            optional_fields=["country_code", "date_of_issue", "date_of_expiry", "gender"],
            requires_mrz=False,
            standard_name="Generic National Identity Standard",
            is_generic_fallback=True,
            description="Generic fallback rule for national identity cards."
        ))

        # 6. USA Visa
        self.register_rule(DocumentRule(
            rule_id="RULE_VISA_USA",
            document_type="visa",
            country_code="USA",
            doc_number_pattern=r"^[A-Z0-9]{8}$",
            min_length=8,
            max_length=8,
            allowed_characters_desc="8 alphanumeric characters",
            mandatory_fields=["document_number", "name", "date_of_birth", "date_of_issue", "date_of_expiry"],
            optional_fields=["country_code", "visa_type", "stay_duration", "entry_validity"],
            requires_mrz=False,
            standard_name="ICAO Doc 9303 Part 7 (MRV)",
            is_generic_fallback=False,
            description="Official United States Visa standard (MRV-A/B)."
        ))

        # 7. USA National ID / State ID
        self.register_rule(DocumentRule(
            rule_id="RULE_NATIONAL_ID_USA",
            document_type="national_id",
            country_code="USA",
            doc_number_pattern=r"^[A-Z0-9]{6,12}$",
            min_length=6,
            max_length=12,
            allowed_characters_desc="6 to 12 alphanumeric characters",
            mandatory_fields=["document_number", "name", "date_of_birth"],
            optional_fields=["country_code", "date_of_issue", "date_of_expiry", "gender"],
            requires_mrz=False,
            standard_name="AAMVA / Real ID Standard",
            is_generic_fallback=False,
            description="United States Real ID specification."
        ))

        # 8. India Driving Licence
        self.register_rule(DocumentRule(
            rule_id="RULE_DRIVING_LICENCE_IND",
            document_type="driving_licence",
            country_code="IND",
            doc_number_pattern=r"^[A-Z0-9]{8,16}$",
            min_length=8,
            max_length=16,
            allowed_characters_desc="8 to 16 alphanumeric characters (Sarathi specification)",
            mandatory_fields=["document_number", "name", "date_of_birth", "date_of_expiry"],
            optional_fields=["date_of_issue", "country_code"],
            requires_mrz=False,
            standard_name="MoRTH Sarathi / ISO/IEC 18013",
            is_generic_fallback=False,
            description="Official Indian Driving Licence standard under Sarathi / MoRTH."
        ))

        # 9. Generic Driving Licences
        self.register_rule(DocumentRule(
            rule_id="RULE_DRIVING_LICENCE_GENERIC",
            document_type="driving_licence",
            country_code=None,
            doc_number_pattern=r"^[A-Z0-9]{6,20}$",
            min_length=6,
            max_length=20,
            allowed_characters_desc="6 to 20 alphanumeric characters",
            mandatory_fields=["document_number", "name", "date_of_birth", "date_of_expiry"],
            optional_fields=["date_of_issue", "country_code"],
            requires_mrz=False,
            standard_name="ISO/IEC 18013 (Generic Driving Licence)",
            is_generic_fallback=True,
            description="Generic fallback rule for motor vehicle driving licences."
        ))

        # 10. Generic Permits
        self.register_rule(DocumentRule(
            rule_id="RULE_PERMIT_GENERIC",
            document_type="permit",
            country_code=None,
            doc_number_pattern=r"^[A-Z0-9]{5,20}$",
            min_length=5,
            max_length=20,
            allowed_characters_desc="5 to 20 alphanumeric characters",
            mandatory_fields=["document_number", "name", "date_of_expiry"],
            optional_fields=["date_of_issue", "country_code", "date_of_birth"],
            requires_mrz=False,
            standard_name="Generic Government Permit Standard",
            is_generic_fallback=True,
            description="Generic fallback rule for residence/work permits."
        ))
