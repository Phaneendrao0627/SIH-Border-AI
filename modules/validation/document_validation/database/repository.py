"""
SQLite repository layer for mock blacklist, watchlist, and identity registry.
"""
from dataclasses import dataclass
from datetime import datetime
import os
import sqlite3
from typing import Any, Dict, List, Optional, Tuple

from document_validation.core.normalizer import normalize_document_number, normalize_string
from document_validation.core.privacy import mask_document_number, mask_name, mask_date


@dataclass
class LookupResult:
    hit: bool
    record: Optional[Dict[str, Any]]
    error: Optional[str] = None


class BorderSecurityRepository:
    """
    Safely executes queries against local mock SQLite border security database.
    Contains fabricated demo data only.
    """

    def __init__(self, db_path: str, timeout: float = 5.0):
        self.db_path = db_path
        self.timeout = timeout

    def _get_connection(self) -> sqlite3.Connection:
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Database file not found at '{self.db_path}'")
        conn = sqlite3.connect(self.db_path, timeout=self.timeout)
        conn.row_factory = sqlite3.Row
        return conn

    def check_blacklist(self, doc_number: str) -> LookupResult:
        """
        Queries blacklist by exact and normalized document number.
        """
        if not doc_number:
            return LookupResult(hit=False, record=None)

        clean_num = normalize_document_number(doc_number)

        try:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT document_number, country_code, reason, date_added, status, source_label
                    FROM blacklist_documents
                    WHERE UPPER(REPLACE(REPLACE(document_number, ' ', ''), '-', '')) = ?
                    """,
                    (clean_num,)
                )
                row = cursor.fetchone()
                if row:
                    data = dict(row)
                    data["masked_document_number"] = mask_document_number(data["document_number"])
                    return LookupResult(hit=True, record=data)
                return LookupResult(hit=False, record=None)
            finally:
                conn.close()

        except (sqlite3.Error, FileNotFoundError, OSError) as e:
            return LookupResult(hit=False, record=None, error=f"Database lookup failed: {str(e)}")

    def check_watchlist(self, name: str, dob: str) -> LookupResult:
        """
        Queries watchlist for name and date of birth match.
        """
        if not name or not dob:
            return LookupResult(hit=False, record=None)

        clean_name = normalize_string(name).upper()
        clean_dob = dob.strip()

        try:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT name, date_of_birth, nationality, reason, date_added, status, source_label
                    FROM watchlist_identities
                    WHERE UPPER(name) = ? AND (date_of_birth = ? OR REPLACE(date_of_birth, '/', '-') = REPLACE(?, '/', '-'))
                    """,
                    (clean_name, clean_dob, clean_dob)
                )
                row = cursor.fetchone()
                if row:
                    data = dict(row)
                    data["masked_name"] = mask_name(data["name"])
                    data["masked_dob"] = mask_date(data["date_of_birth"])
                    return LookupResult(hit=True, record=data)
                return LookupResult(hit=False, record=None)
            finally:
                conn.close()

        except (sqlite3.Error, FileNotFoundError, OSError) as e:
            return LookupResult(hit=False, record=None, error=f"Watchlist lookup error: {str(e)}")

    def find_duplicate_identities(self, name: str, dob: str, current_doc_number: str) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Finds distinct document numbers associated with the same person (Name + DOB).
        """
        if not name or not dob:
            return [], None

        clean_name = normalize_string(name).upper()
        clean_dob = dob.strip()
        clean_curr_num = normalize_document_number(current_doc_number)

        try:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT document_number, document_type, nationality, date_of_expiry, status
                    FROM registered_documents
                    WHERE UPPER(name) = ? AND (date_of_birth = ? OR REPLACE(date_of_birth, '/', '-') = REPLACE(?, '/', '-'))
                    """,
                    (clean_name, clean_dob, clean_dob)
                )
                rows = cursor.fetchall()
                matched = []
                for r in rows:
                    doc_item = dict(r)
                    item_num = normalize_document_number(doc_item["document_number"])
                    doc_item["is_current_document"] = (item_num == clean_curr_num)
                    doc_item["masked_document_number"] = mask_document_number(doc_item["document_number"])
                    matched.append(doc_item)
                return matched, None
            finally:
                conn.close()

        except (sqlite3.Error, FileNotFoundError, OSError) as e:
            return [], f"Duplicate identity lookup error: {str(e)}"
