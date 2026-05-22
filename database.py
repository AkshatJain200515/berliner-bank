import sqlite3
import datetime


DB_PATH = "berliner_bank.db"


def get_db():
    """Opens a connection to the SQLite database and creates tables if they don't exist yet."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username      TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            salt          TEXT NOT NULL,
            mfa_seed      TEXT NOT NULL,
            balance       REAL    DEFAULT 1000.0,
            failed_logins INTEGER DEFAULT 0,
            locked_until  TEXT,
            created_at    TEXT
        )
    """)

    # Add created_at to existing databases that were created before this column existed
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN created_at TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass  # Column already exists, nothing to do

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            sender      TEXT NOT NULL,
            recipient   TEXT NOT NULL,
            amount      REAL NOT NULL,
            timestamp   TEXT NOT NULL,
            mac         TEXT NOT NULL,
            risk_flag   TEXT NOT NULL DEFAULT 'NORMAL'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            event     TEXT NOT NULL,
            detail    TEXT,
            logged_at TEXT NOT NULL
        )
    """)

    conn.commit()
    return conn


# Alias so setup.py can call init_db() to pre-create the schema
def init_db():
    conn = get_db()
    conn.close()


def log_event(event_type, detail=""):
    """
    Writes a security-relevant event to both the audit_log table and stdout.
    Covers logins, failures, lockouts, transfers, and registrations.
    """
    now = datetime.datetime.now().isoformat()
    print(f"[AUDIT | {event_type}] {detail}")

    try:
        conn = get_db()
        conn.execute(
            "INSERT INTO audit_log (event, detail, logged_at) VALUES (?, ?, ?)",
            (event_type, detail, now)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[AUDIT LOG ERROR] Could not persist audit entry: {e}")