import re

def detect_sensitive_data(text):
    patterns = {
        "email": r"[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+",
        "phone": r"\b\d{10}\b",
        "credit_card": r"\b\d{16}\b"
    }

    results = {}

    for key, pattern in patterns.items():
        matches = re.findall(pattern, text)
        if matches:
            results[key] = matches

    return results