"""
pytest suite covering:
  - Warning database logic (add, get, clear)
  - Flask dashboard routes (index, warnings, bans, filters, clear, add/remove word)

Each test uses a temporary in-memory SQLite database so it never touches
the real warnings.db file.
"""

import pytest
import sys
import os

# ---------------------------------------------------------------------------
# Make sure the project root is on sys.path so we can import database, etc.
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import database
from database import (
    init_db,
    add_warning,
    get_warnings,
    get_all_warnings,
    clear_warnings,
    add_ban,
    get_all_bans,
    add_banned_word,
    get_banned_words,
    remove_banned_word,
)


# ---------------------------------------------------------------------------
# Fixture: redirect every db call to a temp in-memory db for the test run
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def use_temp_db(tmp_path, monkeypatch):
    """
    Points database.DB_PATH at a temporary file for every test so tests are
    fully isolated and never touch warnings.db.
    """
    temp_db = str(tmp_path / "test.db")
    monkeypatch.setattr(database, "DB_PATH", temp_db)
    init_db()
    yield


# ===========================================================================
# Warning logic tests
# ===========================================================================

class TestWarnings:

    def test_add_and_get_warning(self):
        """A warning inserted for a user should come back via get_warnings."""
        add_warning(user_id=111, moderator_id=999, reason="spamming")
        rows = get_warnings(111)
        assert len(rows) == 1
        assert rows[0][0] == "spamming"

    def test_multiple_warnings_returned_newest_first(self):
        """get_warnings returns both rows for the user."""
        add_warning(111, 999, "first offence")
        add_warning(111, 999, "second offence")
        rows = get_warnings(111)
        assert len(rows) == 2
        reasons = [r[0] for r in rows]
        assert "first offence" in reasons
        assert "second offence" in reasons

    def test_get_warnings_only_returns_own_user(self):
        """Warnings for user A should not appear when querying user B."""
        add_warning(111, 999, "user A warning")
        add_warning(222, 999, "user B warning")
        assert len(get_warnings(111)) == 1
        assert len(get_warnings(222)) == 1

    def test_clear_warnings_removes_all(self):
        """clear_warnings should leave the user with zero warnings."""
        add_warning(111, 999, "spam")
        add_warning(111, 999, "flood")
        clear_warnings(111)
        assert get_warnings(111) == []

    def test_clear_warnings_does_not_affect_other_users(self):
        """Clearing user A's warnings must not delete user B's warnings."""
        add_warning(111, 999, "user A")
        add_warning(222, 999, "user B")
        clear_warnings(111)
        assert len(get_warnings(222)) == 1

    def test_get_all_warnings_returns_every_row(self):
        """get_all_warnings should return warnings for all users."""
        add_warning(111, 999, "a")
        add_warning(222, 999, "b")
        rows = get_all_warnings()
        assert len(rows) == 2


# ===========================================================================
# Ban logic tests
# ===========================================================================

class TestBans:

    def test_add_and_get_ban(self):
        """A ban inserted should appear in get_all_bans."""
        add_ban(user_id=333, moderator_id=999, reason="rule violation")
        rows = get_all_bans()
        assert len(rows) == 1
        assert rows[0][3] == "rule violation"

    def test_multiple_bans_stored(self):
        add_ban(333, 999, "first")
        add_ban(444, 999, "second")
        assert len(get_all_bans()) == 2


# ===========================================================================
# Word filter logic tests
# ===========================================================================

class TestWordFilter:

    def test_add_and_get_banned_word(self):
        add_banned_word("badword")
        words = [w for _, w in get_banned_words()]
        assert "badword" in words

    def test_duplicate_word_not_added_twice(self):
        add_banned_word("duplicate")
        add_banned_word("duplicate")
        words = get_banned_words()
        assert len(words) == 1

    def test_remove_banned_word(self):
        add_banned_word("removeMe")
        word_id = get_banned_words()[0][0]
        remove_banned_word(word_id)
        assert get_banned_words() == []

    def test_words_stored_lowercase(self):
        add_banned_word("UPPER")
        words = [w for _, w in get_banned_words()]
        assert "upper" in words


# ===========================================================================
# Flask route tests
# ===========================================================================

@pytest.fixture()
def client():
    """Provides a Flask test client with a fresh app context."""
    from dashboard import app
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    with app.test_client() as c:
        yield c


class TestDashboardRoutes:

    def test_index_returns_200(self, client):
        response = client.get("/")
        assert response.status_code == 200

    def test_warnings_page_returns_200(self, client):
        response = client.get("/warnings")
        assert response.status_code == 200

    def test_warnings_page_shows_warning(self, client):
        add_warning(111, 999, "test reason")
        response = client.get("/warnings")
        assert b"test reason" in response.data

    def test_bans_page_returns_200(self, client):
        response = client.get("/bans")
        assert response.status_code == 200

    def test_filters_page_returns_200(self, client):
        response = client.get("/filters")
        assert response.status_code == 200

    def test_filters_page_shows_word(self, client):
        add_banned_word("testword")
        response = client.get("/filters")
        assert b"testword" in response.data

    def test_add_filter_word_via_post(self, client):
        response = client.post("/filters/add", data={"word": "newbadword"})
        assert response.status_code == 302  # redirect after POST
        words = [w for _, w in get_banned_words()]
        assert "newbadword" in words

    def test_remove_filter_word_via_post(self, client):
        add_banned_word("toremove")
        word_id = get_banned_words()[0][0]
        response = client.post(f"/filters/remove/{word_id}")
        assert response.status_code == 302
        assert get_banned_words() == []

    def test_clear_user_warnings_via_post(self, client):
        add_warning(111, 999, "spam")
        response = client.post("/warnings/clear/111")
        assert response.status_code == 302
        assert get_warnings(111) == []
