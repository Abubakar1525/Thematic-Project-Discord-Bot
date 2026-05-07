banned_words = [
    "frick",
    "shi",
    "slur",
    "burger",
    "cheese"
    
]

def contains_banned_word(message: str) -> bool:
    lowered = message.lower()
    return any(word in lowered for word in banned_words)
