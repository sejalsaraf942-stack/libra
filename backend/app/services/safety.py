UNSAFE_KEYWORDS = [
    "how to kill", "how to murder", "commit murder", "evade arrest", "forge document",
    "fabricate evidence", "hide black money", "bribe", "find loophole", "avoid punishment",
]


def classify_intent(text: str) -> str:
    t = text.lower()
    if any(k in t for k in UNSAFE_KEYWORDS):
        return "unsafe"
    if len(text.split()) < 4:
        return "vague"
    return "safe"
