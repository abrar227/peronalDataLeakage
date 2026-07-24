"""
detectors/rule_based.py

Rule-based (regex) detection component.
Covers SRS section 4.6.2: known, structured patterns such as
emails, phone numbers, credential and financial-data patterns.
"""

import re


# ---------- PATTERNS ----------

PATTERNS = {
    "email": re.compile(
        r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-z]{2,}'
    ),
    "phone": re.compile(
        r'\b\+?\d{1,3}?[-.\s]?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b'
    ),
    "credit_card": re.compile(
        r'\b(?:\d[ -]*?){13,16}\b'
    ),
    "ssn": re.compile(
        r'\b\d{3}-\d{2}-\d{4}\b'
    ),
    "aadhaar": re.compile(
        r'\b\d{4}\s\d{4}\s\d{4}\b'
    ),
    "ip_address": re.compile(
        r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
    ),
    "password": re.compile(
        r'(?i)\b(?:password|passwd|pwd)\s*[:=]\s*\S+'
    ),
    "api_key": re.compile(
        r'(?i)\b(?:api[_-]?key|secret[_-]?key|access[_-]?token|token)\s*[:=]\s*[A-Za-z0-9_\-]{8,}'
        r'|sk_live_[A-Za-z0-9]{10,}'
        r'|sk_test_[A-Za-z0-9]{10,}'
        r'|AKIA[0-9A-Z]{16}'
    ),
    # Simple street-address heuristic: number + word(s) + street-type keyword.
    # Uses literal spaces (not \s) so it can never cross a newline.
    "address": re.compile(
        r'\b\d{1,5}(?:[ ]+[A-Za-z0-9.]{1,20}){1,4}[ ]+'
        r'(?:Street|St|Road|Rd|Avenue|Ave|Lane|Ln|Drive|Dr|Boulevard|Blvd|Way|Court|Ct)\b',
        re.IGNORECASE,
    ),
}


def _luhn_valid(number: str) -> bool:
    """Luhn checksum, used to cut false positives on credit_card matches."""
    digits = [int(d) for d in number if d.isdigit()]
    if len(digits) < 13 or len(digits) > 19:
        return False
    checksum = 0
    parity = len(digits) % 2
    for i, d in enumerate(digits):
        if i % 2 == parity:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0


def detect_patterns(text: str) -> dict:
    """
    Run all rule-based patterns against the input text.
    Returns a dict of category -> list of unique matches.
    """
    results = {}

    for name, pattern in PATTERNS.items():
        matches = pattern.findall(text)

        if name == "credit_card":
            # findall on a bare-digit-run pattern also matches phone-like
            # or ID-like numbers; keep only Luhn-valid ones.
            matches = [m for m in matches if _luhn_valid(m)]

        # de-duplicate, preserve order
        results[name] = list(dict.fromkeys(m.strip() for m in matches if m.strip()))

    # Aadhaar (XXXX XXXX XXXX) and credit-card numbers can overlap on the
    # same digit run. If a "aadhaar" match is a substring of a confirmed
    # credit_card match, drop it — the credit card classification wins.
    if results.get("credit_card"):
        results["aadhaar"] = [
            a for a in results["aadhaar"]
            if not any(a in cc for cc in results["credit_card"])
        ]

    return results


if __name__ == "__main__":
    sample = (
        "Contact me at john.doe@gmail.com or 987-654-3210.\n"
        "Card: 4111 1111 1111 1111\n"
        "SSN: 123-45-6789\n"
        "Aadhaar: 1234 5678 9012\n"
        "password: Summer2024!\n"
        "api_key: sk_live_51Hn8x7ZQm29fkLp0wQe\n"
        "Server IP: 192.168.1.10\n"
        "Address: 42 Lakeview Street, Springfield"
    )
    from pprint import pprint
    pprint(detect_patterns(sample))
