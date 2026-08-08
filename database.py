import sqlite3

DB_PATH = "warnings.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS warnings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            moderator_id INTEGER NOT NULL,
            reason TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            moderator_id INTEGER NOT NULL,
            reason TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS banned_words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT UNIQUE NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def add_ban(user_id, moderator_id, reason):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO bans (user_id, moderator_id, reason)
        VALUES (?, ?, ?)
    """, (user_id, moderator_id, reason))
    conn.commit()
    conn.close()

def get_warnings(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT reason, timestamp FROM warnings WHERE user_id = ? ORDER BY timestamp DESC
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def clear_warnings(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM warnings WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def add_warning(user_id, moderator_id, reason):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO warnings (user_id, moderator_id, reason)
        VALUES (?, ?, ?)
    """, (user_id, moderator_id, reason))
    conn.commit()
    conn.close()


# --- Used by the web dashboard (dashboard.py) ---
# get_warnings()/above only fetches rows for a single user, which is what the
# Discord commands need. The dashboard needs to list everyone at once, so
# these two functions skip the WHERE clause and return every row instead.

def get_all_warnings():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, user_id, moderator_id, reason, timestamp
        FROM warnings
        ORDER BY timestamp DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_all_bans():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, user_id, moderator_id, reason, timestamp
        FROM bans
        ORDER BY timestamp DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_banned_words():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, word FROM banned_words ORDER BY word")
    rows = cursor.fetchall()
    conn.close()
    return rows

def add_banned_word(word):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO banned_words (word) VALUES (?)", (word.lower().strip(),))
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # word already exists
    conn.close()

def remove_banned_word(word_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM banned_words WHERE id = ?", (word_id,))
    conn.commit()
    conn.close()
