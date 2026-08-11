"""
Web dashboard for the Discord moderation bot.

WHAT THIS FILE DOES
--------------------
This is a small Flask web app that reads the same SQLite database
(warnings.db) that the bot (main.py) writes to. It lets you view warnings,
bans, and the auto-moderation word filter in a browser instead of digging
through Discord commands or opening the .db file by hand.

It is a completely separate process from the bot — you can run the bot
(main.py) and this dashboard (dashboard.py) at the same time, in two
different terminals. They just both happen to read/write the same file.

HOW TO RUN
----------
    pip install -r requirements.txt
    python dashboard.py

Then open http://127.0.0.1:5000 in your browser.

SECURITY NOTE
-------------
There is no login on this dashboard. Anyone who can reach the port it runs
on can see warning/ban history and clear warnings. That's fine for running
it on your own machine, but do not expose it to the public internet as-is.
"""

from flask import Flask, render_template, redirect, url_for, flash, request
from database import init_db, get_all_warnings, get_all_bans, clear_warnings, get_banned_words, add_banned_word, remove_banned_word
import os

# ---------------------------------------------------------------------------
# 1. App setup
# ---------------------------------------------------------------------------
# Flask(__name__) creates the application object; __name__ tells Flask what
# module it lives in so it can find the templates/ and static/ folders next
# to this file.
app = Flask(__name__)

# secret_key is required for flash() to work (Flask signs the flash-message
# cookie with it). It only matters for security if you add real user
# sessions/logins later — for this read-mostly local dashboard, any string
# is fine, but you'd want a random, private value before deploying anywhere.
app.secret_key = "dev-secret-key-change-me"

# Make sure the warnings/bans tables exist before we query them. This is the
# same function main.py calls on startup, so the dashboard works even if you
# run it before ever starting the bot.
init_db()


# ---------------------------------------------------------------------------
# 2. Home page — quick overview / stats
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    """
    Landing page. Shows simple counts so you get a snapshot of moderation
    activity without opening the detail pages.
    """
    warnings = get_all_warnings()
    bans = get_all_bans()

    # A plain dict is enough here — render_template() below passes it to the
    # HTML template, where we read stats.total_warnings, etc.
    stats = {
        "total_warnings": len(warnings),
        "total_bans": len(bans),
        "banned_word_count": len(get_banned_words()),
    }
    return render_template("index.html", stats=stats)


# ---------------------------------------------------------------------------
# 3. Warnings page — table of every warning + a "clear" action per user
# ---------------------------------------------------------------------------
@app.route("/warnings")
def warnings_page():
    """
    Lists every warning stored in the database, newest first. Each row shows
    the Discord user ID that was warned, the moderator (or the bot itself,
    for automatic word-filter warnings) who issued it, why, and when.
    """
    rows = get_all_warnings()
    return render_template("warnings.html", warnings=rows)


@app.route("/warnings/clear/<int:user_id>", methods=["POST"])
def clear_user_warnings(user_id):
    """
    Deletes all warnings for one user. This is the web equivalent of the
    bot's `!clearwarnings @user` command, triggered by the "Clear" button
    next to that user's row on the warnings page.

    It only accepts POST (not GET) so the action can't be triggered just by
    visiting a URL or a search engine/browser prefetching a link.
    """
    clear_warnings(user_id)
    # flash() stores a one-time message that the *next* page render will
    # show (see the {% with messages = get_flashed_messages() %} block in
    # templates/base.html), then redirect() sends the browser back to the
    # warnings list so it can display that message and the updated table.
    flash(f"Cleared all warnings for user {user_id}.")
    return redirect(url_for("warnings_page"))


# ---------------------------------------------------------------------------
# 4. Bans page — read-only table of every ban on record
# ---------------------------------------------------------------------------
@app.route("/bans")
def bans_page():
    """
    Lists every ban the bot has logged (issued via the `!ban` command).
    This is read-only: actually unbanning someone requires talking to the
    Discord API, which only the bot process (main.py, via `!unban`) does.
    """
    rows = get_all_bans()
    return render_template("bans.html", bans=rows)


# ---------------------------------------------------------------------------
# 5. Word filter page — shows the list used by auto-moderation
# ---------------------------------------------------------------------------
@app.route("/filters")
def filters_page():
    words = get_banned_words()
    return render_template("filters.html", words=words)


@app.route("/filters/add", methods=["POST"])
def add_filter():
    word = request.form.get("word", "").strip()
    if word:
        add_banned_word(word)
        flash(f'"{word}" added to the word filter.')
    else:
        flash("Please enter a word.")
    return redirect(url_for("filters_page"))


@app.route("/filters/remove/<int:word_id>", methods=["POST"])
def remove_filter(word_id):
    remove_banned_word(word_id)
    flash("Word removed from filter.")
    return redirect(url_for("filters_page"))


# ---------------------------------------------------------------------------
# 6. Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
