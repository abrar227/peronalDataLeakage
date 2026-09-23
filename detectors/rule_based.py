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
        # 1. International separated numbers (with optional country code and/or parentheses):
        #    e.g. 987-654-3210, +1 987-654-3210, (123) 456-7890, +1 (123) 456-7890, 0412 345 678, 91-9876543210
        r'(?:\+?\d{1,4}[-.\s])?\(?\d{2,4}\)?[-.\s]\d{2,4}[-.\s]\d{2,4}(?:[-.\s]\d{1,4})?\b'
        # 2. Indian mobile numbers (starts with 6, 7, 8, or 9; optional +91 or 0 prefix; optional 5-5 split):
        #    e.g. 9876543210, +91 9876543210, +91 98765 43210, 09876543210
        r'|\+91[-\s]?[6-9]\d{4}[-\s]?\d{5}\b'
        r'|(?:\b91[-\s]?|\b0)?[6-9]\d{4}[-\s]?\d{5}\b'
        # 3. North American 10-digit mobile/landline numbers:
        #    e.g. 2125551234, +1-2125551234
        r'|\b[2-9]\d{2}[2-9]\d{6}\b'
        r'|\+1[-.\s]?[2-9]\d{2}[2-9]\d{6}\b'
    ),
    "credit_card": re.compile(
        r'\b(?:\d[ -]*?){13,16}\b'
    ),
    "ssn": re.compile(
        r'\b\d{3}-\d{2}-\d{4}\b'
    ),
    "aadhaar": re.compile(
        # 12 digits: formatted with spaces (1234 5678 9012), hyphens (1234-5678-9012), or contiguous (123456789012)
        r'\b\d{4}[-\s]\d{4}[-\s]\d{4}\b'
        r'|\b\d{12}\b'
    ),
    "ip_address": re.compile(
        r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
    ),
    "password": re.compile(
        r'(?i)\b(?:password|passwd|pwd)\b.{0,40}?(?:is|[:=])\s*\S+'
    ),
    "api_key": re.compile(
        r'(?i)\b(?:api[_-]?key|secret[_-]?key|access[_-]?token|token)\s*[:=]\s*[A-Za-z0-9_\-]{8,}'
        r'|sk_live_[A-Za-z0-9]{10,}'
        r'|sk_test_[A-Za-z0-9]{10,}'
        r'|AKIA[0-9A-Z]{16}'
    ),
    # Simple street-address heuristic: number + word(s) + street-type keyword.
    # Uses literal spaces (not \s) so it can never cross a newline.
    "passport": re.compile(
        r'(?i)\b(?:passport(?:\s+no\.?|\s+number)?\s*[:=is]*\s*)([a-z0-9]{7,9})\b'
    ),
    "medical": re.compile(
        r'(?i)\b(?:medical leave|surgery|diagnosis|medical record|prescription|hospitalized|hypertension|diagnosed|disease|syndrome)\b'
    ),
    "driver_license": re.compile(
        r'(?i)\b(?:driver\'?s?\s+license)(?:\s+number)?\s*[:=is]*\s*([A-Z0-9]{5,20})\b'
    ),
    "security_question": re.compile(
        r'(?i)\b(?:security\s+question|maiden\s+name|first\s+pet|city\s+of\s+birth)\b'
    ),
    "address": re.compile(
        r'\b\d{1,5}(?:[ ]+[A-Za-z0-9.]{1,20}){1,4}[ ]+'
        r'(?:Street|St|Road|Rd|Avenue|Ave|Lane|Ln|Drive|Dr|Boulevard|Blvd|Way|Court|Ct)\b',
        re.IGNORECASE,
    ),
}


def _phone_confidence(value: str) -> float:
    """
    A matched 'phone-shaped' string could genuinely be a phone number,
    or could be an order ID, a room+time combo, a random code, etc.
    Score it higher when the match has a strong phone-specific signal
    (country code, valid Indian mobile prefix), lower for the generic
    separated-digits fallback pattern.
    """
    stripped = value.strip()
    digits = re.sub(r"\D", "", stripped)

    if stripped.startswith("+91") or (digits.startswith("91") and len(digits) == 12):
        return 0.9
    if len(digits) == 10 and digits[0] in "6789":
        return 0.85
    if stripped.startswith("+"):
        return 0.8
    return 0.55  # generic NN-NNN-NNNN shape - easy to confuse with other codes


def _aadhaar_confidence(value: str) -> float:
    """
    The spaced/hyphenated 4-4-4 layout is the canonical way Aadhaar
    numbers are displayed, so it's a fairly strong signal. A bare
    12-digit run with no separators is far more ambiguous - it could
    be almost any numeric ID, order code, or phone-like string.
    """
    if re.search(r"[-\s]", value):
        return 0.8
    return 0.45


def _ip_confidence(value: str) -> float:
    """Confidence is high only if every octet is a valid 0-255 byte."""
    parts = value.split(".")
    try:
        if len(parts) == 4 and all(0 <= int(p) <= 255 for p in parts):
            return 0.85
    except ValueError:
        pass
    return 0.4


def _credit_card_confidence(value: str) -> float:
    """Already Luhn-validated by the time this runs, so baseline is high."""
    digits = re.sub(r"\D", "", value)
    return 0.95 if len(digits) == 16 else 0.8


def _api_key_confidence(value: str) -> float:
    """A recognized provider prefix (sk_live_, AKIA...) is a near-certain signal."""
    if re.search(r"sk_live_|sk_test_|AKIA", value):
        return 0.95
    return 0.85  # matched via explicit api_key:/token: keyword


def _password_confidence(value: str) -> float:
    """
    'password:' / 'password=' is an explicit key-value assignment - a
    strong, near-unambiguous signal. 'password is X' is looser phrasing
    that can also show up in sentences that aren't actually revealing a
    secret at all (e.g. "the password is not shared with anyone"). This
    checks what was actually captured after the keyword and scores
    accordingly, instead of treating every match the same.
    """
    m = re.search(r'(?i)(?:password|passwd|pwd)\b.{0,40}?(?:is|[:=])\s*(\S+)', value)
    revealed = m.group(1).lower().strip(".,!?") if m else ""

    non_secret_words = {
        "not", "never", "unknown", "hidden", "secret", "forgotten",
        "same", "unchanged", "blank", "empty", "required", "optional",
        "reset", "changed", "set", "still", "also", "different", "the",
    }
    if revealed in non_secret_words:
        return 0.2  # almost certainly discussing passwords, not revealing one

    if re.search(r'[:=]\s*\S', value):
        return 0.9  # explicit key:value assignment

    return 0.65  # looser "password is X" phrasing - plausible but noisier


# Categories whose confidence doesn't depend on the matched value itself -
# the pattern requiring an explicit keyword (password:, or a strict
# XXX-XX-XXXX shape) already does most of the disambiguating work.
FIXED_CONFIDENCE = {
    "email": 0.95,
    "ssn": 0.85,
    "passport": 0.90,
    "medical": 0.85,
    "driver_license": 0.90,
    "security_question": 0.80,
    "address": 0.65,
}


def _score_match(category: str, value: str) -> float:
    """Returns a 0.0-1.0 confidence that this match is genuinely that category of PII."""
    if category == "phone":
        return _phone_confidence(value)
    if category == "aadhaar":
        return _aadhaar_confidence(value)
    if category == "ip_address":
        return _ip_confidence(value)
    if category == "credit_card":
        return _credit_card_confidence(value)
    if category == "api_key":
        return _api_key_confidence(value)
    if category == "password":
        return _password_confidence(value)
    return FIXED_CONFIDENCE.get(category, 0.7)


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
    Uses span-based conflict resolution so overlapping text is assigned
    to the most specific category (Credit Card > Aadhaar > SSN > IP > Phone).
    Returns a dict of category -> list of unique matches.
    """
    raw_spans = {}

    for name, pattern in PATTERNS.items():
        spans = []
        for m in pattern.finditer(text):
            val = m.group().strip()
            if not val:
                continue
            if name == "credit_card" and not _luhn_valid(val):
                continue
            if name == "phone":
                prefix = text[max(0, m.start() - 20):m.start()].lower()
                if re.search(r'\b(?:gate|flight|id|order|invoice|receipt|account|amount|rs|inr|usd|\$|date)\s*#?\s*$', prefix):
                    continue
            spans.append((m.start(), m.end(), val))
        raw_spans[name] = spans

    # Aadhaar vs Credit Card overlap: Credit Card wins
    if raw_spans.get("credit_card") and raw_spans.get("aadhaar"):
        raw_spans["aadhaar"] = [
            a for a in raw_spans["aadhaar"]
            if not any(
                max(a[0], cc[0]) < min(a[1], cc[1])
                for cc in raw_spans["credit_card"]
            )
        ]

    # Specific categories take precedence over Phone matches at the same text position
    higher_priority_spans = (
        raw_spans.get("credit_card", [])
        + raw_spans.get("aadhaar", [])
        + raw_spans.get("ssn", [])
        + raw_spans.get("ip_address", [])
        + raw_spans.get("password", [])
        + raw_spans.get("api_key", [])
    )
    if higher_priority_spans and raw_spans.get("phone"):
        raw_spans["phone"] = [
            p for p in raw_spans["phone"]
            if not any(
                max(p[0], hp[0]) < min(p[1], hp[1])
                for hp in higher_priority_spans
            )
        ]

    results = {}
    for name in PATTERNS.keys():
        seen = {}
        for span in raw_spans.get(name, []):
            value = span[2]
            conf = _score_match(name, value)
            # Drop structurally valid but semantically invalid IP addresses entirely
            if name == "ip_address" and conf < 0.5:
                continue
            if value not in seen:
                seen[value] = {"value": value, "confidence": round(conf, 2)}
        results[name] = list(seen.values())

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
