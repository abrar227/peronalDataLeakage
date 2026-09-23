import re

def detect_sensitive_data(text):
    patterns = {
        "email": r"[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+",
        "phone": (
            r'(?:\+?\d{1,4}[-.\s])?\(?\d{2,4}\)?[-.\s]\d{2,4}[-.\s]\d{2,4}(?:[-.\s]\d{1,4})?'
            r'|(?:\+?91[-\s]?|0)?[6-9]\d{4}[-\s]?\d{5}'
            r'|(?:\+?1[-\s]?)?[2-9]\d{2}[2-9]\d{6}'
        ),
        "credit_card": r"\b(?:\d[ -]*?){13,16}\b",
        "aadhaar": r"\b\d{4}[-\s]\d{4}[-\s]\d{4}\b|\b\d{12}\b",
    }

    results = {}

    for key, pattern in patterns.items():
        matches = re.findall(pattern, text)
        if matches:
            results[key] = list(dict.fromkeys(m.strip() for m in matches if m.strip()))

    if results.get("aadhaar") and results.get("phone"):
        aadhaar_digits = {''.join(c for c in a if c.isdigit()) for a in results["aadhaar"]}
        results["phone"] = [
            p for p in results["phone"]
            if ''.join(c for c in p if c.isdigit()) not in aadhaar_digits
        ]

    return results