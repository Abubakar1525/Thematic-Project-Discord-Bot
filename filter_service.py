banned_words = [
    "badword1",
    "badword2",
]

def contains_banned_word(message: str) -> bool:
    lowered = message.lower()
    return any(word in lowered for word in banned_words)
