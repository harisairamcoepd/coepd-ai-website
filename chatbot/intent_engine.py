INTENT_KEYWORDS: dict[str, tuple[str, ...]] = {
    "book_demo": ("book free demo", "book demo", "demo", "call me", "register"),
    "program_benefits": (
        "program benefits",
        "benefits",
        "advantages",
        "why join",
        "why this program",
    ),
    "internship": ("internship", "intern"),
    "placement_support": ("placement support", "placement program", "which program includes placement", "bjm platform"),
    "fees": (
        "fee",
        "fees",
        "price",
        "cost",
        "amount",
        "payment",
        "course fee",
        "course fees",
        "program fee",
        "program cost",
        "how much",
        "pricing",
        "training fee",
        "ba training cost",
        "payment details",
    ),
    "duration": ("duration", "how long", "timeline", "months"),
    "placement": ("placement", "jobs", "career support", "interview"),
    "batch_timings": ("batch", "timings", "weekend", "weekday"),
    "course_details": ("course details", "course structure", "curriculum", "syllabus", "what will i learn", "program information", "course info", "training program", "ba training", "program details"),
}


def detect_intent(message: str) -> str:
    text = (message or "").lower().strip()
    for intent, words in INTENT_KEYWORDS.items():
        if any(word in text for word in words):
            return intent
    return "unknown"
