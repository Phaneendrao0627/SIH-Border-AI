"""
Base validator interface.
"""
from abc import ABC, abstractmethod
from typing import List, Tuple

from document_validation.core.normalizer import NormalizedInput
from document_validation.core.rule_registry import DocumentRule
from document_validation.models.flags import ValidationFlag
from document_validation.models.result_model import FieldResult


class BaseValidator(ABC):
    """Abstract base class for all independent validators."""

    @abstractmethod
    def validate(
        self,
        norm_input: NormalizedInput,
        rule: DocumentRule,
        **kwargs
    ) -> Tuple[List[FieldResult], List[ValidationFlag], List[str]]:
        """
        Executes validation.
        Returns:
            - List of FieldResult objects
            - List of raised ValidationFlag enums
            - List of human-readable explanation strings
        """
        pass
