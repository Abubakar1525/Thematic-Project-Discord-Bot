"""
Seed script — fills warnings.db with a handful of realistic sample records.

WHAT THIS DOES
--------------
A freshly cloned copy of this repo has little or no data in warnings.db,
which makes the dashboard (dashboard.py) look empty. This script wipes the
warnings/bans/banned_words tables and inserts a small set of
fake-but-realistic moderation records — a couple of manual warnings, a
couple of automatic word-filter warnings, a ban, and a handful of filtered
words — so there's something to look at right away.

It reuses the exact same database.py functions the bot itself calls
(init_db, add_warning, add_ban, add_banned_word), so the rows it creates
look exactly like rows the real bot would have produced.

HOW TO RUN
----------
    python seed_data.py

Safe to re-run: it clears the warnings/bans/banned_words tables first, so
running it twice won't pile up duplicate rows.
"""

import sqlite3
from database import DB_PATH, init_db, add_warning, add_ban, add_banned_word

# ---------------------------------------------------------------------------
# Fake Discord user/moderator IDs.
# Real Discord IDs ("snowflakes") are large integers; these are made up but
# formatted the same way so the dashboard reads naturally.
# ---------------------------------------------------------------------------
ALICE = 812345678901234567
BOB = 823456789012345678
CARL = 834567890123456789
MOD_JORDAN = 745678901234567890
BOT_ID = 756789012345678901  # stands in for the bot's own user ID, which is
                              # what main.py uses as the "moderator" on
                              # automatic, filter-triggered warnings


SAMPLE_FILTERED_WORDS = ["frick", "shi", "slur", "scammer-link", "raid"]


def reset_tables():
    """Wipe existing rows so this script can be re-run without piling
    seed data on top of whatever was already there."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM warnings")
    cursor.execute("DELETE FROM bans")
    cursor.execute("DELETE FROM banned_words")
    conn.commit()
    conn.close()


def seed():
    init_db()  # make sure the tables exist, same call main.py makes on startup
    reset_tables()

    # --- Manual warnings: the kind issued via `!warn @user <reason>` ---
    add_warning(ALICE, MOD_JORDAN, "Spamming invite links in #general")
    add_warning(BOB, MOD_JORDAN, "Arguing with a moderator's decision in public")

    # --- Automatic warnings: the kind on_message() in main.py issues when
    # a message trips the word filter. The reason string matches main.py
    # exactly so these look identical to real ones. ---
    add_warning(CARL, BOT_ID, "Automatic: banned word used")
    add_warning(ALICE, BOT_ID, "Automatic: banned word used")

    # --- A ban: the kind issued via `!ban @user <reason>` ---
    add_ban(BOB, MOD_JORDAN, "Repeated harassment after multiple warnings")

    # --- Filtered words: the banned_words table shown/managed on the
    # dashboard's Word Filter page (dashboard.py's /filters routes). ---
    for word in SAMPLE_FILTERED_WORDS:
        add_banned_word(word)

    print(
        f"Seeded warnings.db with 4 warnings, 1 ban, "
        f"and {len(SAMPLE_FILTERED_WORDS)} filtered words."
    )


if __name__ == "__main__":
    seed()
