import sqlite3

DB_PATH = "database.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content_id TEXT NOT NULL,
            submitted_at TEXT NOT NULL,
            content_preview TEXT,
            llm_score REAL,
            stylometric_score REAL,
            combined_score REAL,
            attribution_result TEXT,
            confidence_label TEXT,
            transparency_label TEXT,
            status TEXT DEFAULT 'reviewed'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS appeals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content_id TEXT NOT NULL,
            appealed_at TEXT NOT NULL,
            creator_reasoning TEXT,
            status TEXT DEFAULT 'under_review'
        )
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized.")
