"""
Database schema creation and synthetic dataset seeder.
All data is strictly synthetic and fabricated for hackathon prototype demonstration.
"""
from datetime import datetime
import os
import sqlite3
from typing import Optional


def seed_mock_database(db_path: str) -> None:
    """
    Initializes and seeds the mock border security SQLite database.
    """
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Blacklist Documents Table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS blacklist_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_number TEXT UNIQUE NOT NULL,
            country_code TEXT,
            reason TEXT NOT NULL,
            date_added TEXT NOT NULL,
            status TEXT NOT NULL,
            source_label TEXT NOT NULL
        )
        """
    )

    # 2. Watchlist Identities Table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS watchlist_identities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            date_of_birth TEXT NOT NULL,
            nationality TEXT,
            reason TEXT NOT NULL,
            date_added TEXT NOT NULL,
            status TEXT NOT NULL,
            source_label TEXT NOT NULL
        )
        """
    )

    # 3. Registered Documents (For duplicate identity detection)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS registered_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_number TEXT UNIQUE NOT NULL,
            document_type TEXT NOT NULL,
            name TEXT NOT NULL,
            date_of_birth TEXT NOT NULL,
            nationality TEXT,
            date_of_expiry TEXT,
            date_registered TEXT NOT NULL,
            status TEXT NOT NULL
        )
        """
    )

    # Clean previous demo entries to ensure consistent idempotence
    cursor.execute("DELETE FROM blacklist_documents")
    cursor.execute("DELETE FROM watchlist_identities")
    cursor.execute("DELETE FROM registered_documents")

    today_str = datetime.now().strftime("%Y-%m-%d")

    # --- Seed Blacklist Documents (Fabricated) ---
    blacklist_samples = [
        ("X9988776", "IND", "Reported lost/stolen by holder at Mumbai airport", today_str, "ACTIVE", "SIM_NCB_ALERT"),
        ("M9999999", "IND", "Suspected counterfeit batch series alert", today_str, "ACTIVE", "SIM_IMMIGRATION_BUREAU"),
        ("B7654321", "IND", "Revoked due to court order / impounded", today_str, "ACTIVE", "SIM_COURT_DIRECTIVE"),
        ("U12345678", "USA", "Lost document reported to consular services", today_str, "ACTIVE", "SIM_CONSULAR_WATCH"),
        ("K8765432", "GBR", "Flagged stolen blank passport stock", today_str, "ACTIVE", "SIM_BORDER_FORCE"),
        ("D98765432", "DEU", "Reported destroyed / invalid document", today_str, "ACTIVE", "SIM_POLIZEI_ALERT"),
        ("IND-LOST-8899", "IND", "Seized fraudulent document copy", today_str, "ACTIVE", "SIM_CUSTOMS_ALERT"),
    ]

    cursor.executemany(
        """
        INSERT INTO blacklist_documents (document_number, country_code, reason, date_added, status, source_label)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        blacklist_samples
    )

    # --- Seed Watchlist Identities (Fabricated) ---
    watchlist_samples = [
        ("VIKRAM SINGH", "1985-11-20", "IND", "Simulated Interpol Red Notice subject", today_str, "ACTIVE", "SIM_INTERPOL_RED"),
        ("MARCUS VANCE", "1979-03-14", "USA", "Financial cybercrime suspect under active warrant", today_str, "ACTIVE", "SIM_WARRANT_LIST"),
        ("TARIQ AHMED", "1992-06-18", "CAN", "Document fraud syndicate investigation subject", today_str, "ACTIVE", "SIM_BORDER_INVESTIGATION"),
        ("SOPHIA MARTINEZ", "1988-09-05", "FRA", "Travel ban restriction order", today_str, "ACTIVE", "SIM_IMMIGRATION_BAN"),
        ("ARJUN REDDY", "2001-05-10", "IND", "Fabricated test watchlist identity for prototype verification", today_str, "FLAGGED", "SIM_TEST_FLAG"),
    ]

    cursor.executemany(
        """
        INSERT INTO watchlist_identities (name, date_of_birth, nationality, reason, date_added, status, source_label)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        watchlist_samples
    )

    # --- Seed Registered Documents (For duplicate detection & clean verification) ---
    registered_samples = [
        # Normal single-doc identities
        ("A1234567", "passport", "RAHUL KUMAR", "2002-04-12", "IND", "2030-08-15", today_str, "VERIFIED"),
        ("P4567890", "passport", "PRIYA SHARMA", "1996-05-22", "IND", "2032-12-31", today_str, "VERIFIED"),
        ("987654321", "passport", "JOHN DOE", "1990-01-01", "USA", "2029-05-10", today_str, "VERIFIED"),
        ("G3456789", "passport", "ANITA DESHMUKH", "1998-11-03", "IND", "2031-07-20", today_str, "VERIFIED"),
        ("DL9922110", "driving_licence", "AMIT PATEL", "1987-08-14", "IND", "2035-08-14", today_str, "VERIFIED"),
        ("NID443322", "national_id", "SARAH CONNOR", "1984-02-28", "USA", "2034-02-28", today_str, "VERIFIED"),

        # Duplicate Identity Case 1: ELENA ROSTOVA has 3 distinct document numbers across doc types
        ("F1122334", "passport", "ELENA ROSTOVA", "1990-07-15", "FRA", "2031-06-30", today_str, "ACTIVE"),
        ("F5566778", "national_id", "ELENA ROSTOVA", "1990-07-15", "FRA", "2030-01-15", today_str, "ACTIVE"),
        ("F9988112", "permit", "ELENA ROSTOVA", "1990-07-15", "FRA", "2028-11-10", today_str, "ACTIVE"),

        # Duplicate Identity Case 2: RAJESH GUPTA has 2 distinct passport numbers
        ("Z1029384", "passport", "RAJESH GUPTA", "1983-02-28", "IND", "2030-04-10", today_str, "ACTIVE"),
        ("Z9871234", "passport", "RAJESH GUPTA", "1983-02-28", "IND", "2032-09-18", today_str, "ACTIVE"),
    ]

    cursor.executemany(
        """
        INSERT INTO registered_documents (document_number, document_type, name, date_of_birth, nationality, date_of_expiry, date_registered, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        registered_samples
    )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    db_file = os.path.join(os.path.dirname(__file__), "mock_border.db")
    seed_mock_database(db_file)
    print(f"Mock border security database seeded successfully at: {db_file}")
