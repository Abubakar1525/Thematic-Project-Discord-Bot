# Thematic-Project-Discord-Bot
Making a discord bot for uni

## Web Dashboard

A small Flask app (`dashboard.py`) lets you view warnings, bans, and the
word filter list in a browser instead of the database file directly. It
reads the same `warnings.db` that the bot uses, and runs as a separate
process from the bot.

```bash
pip install -r requirements.txt
python dashboard.py
```

Then open http://127.0.0.1:5000. See the comments at the top of
`dashboard.py` for how each part works.
