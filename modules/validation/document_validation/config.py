"""
Configuration manager for Document Validation Engine.
"""
from dataclasses import dataclass
from datetime import date
import os
from typing import Optional


@dataclass
class ValidationConfig:
    db_path: str = os.path.join(
        os.path.dirname(__file__), "database", "mock_border.db"
    )
    db_timeout: float = 5.0
    expiring_soon_threshold_days: int = 180
    min_mrz_confidence: float = 0.80
    min_ocr_confidence: float = 0.70
    enable_database_checks: bool = True
    enable_privacy_masking: bool = True
    validation_date: Optional[date] = None
    validator_version: str = "2.0.0"
