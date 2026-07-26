"""
detectors/risk_scoring.py

Computes a risk score from combined detector output.
Weighted by category severity, plus a bonus when multiple
categories co-occur (e.g. a name + phone together is riskier
than either alone, since it's more easily linked to a person).
"""

# Base severity weight per category (tune these as you calibrate
# against your labelled dataset).
CATEGORY_WEIGHTS = {
    "email": 15,
    "phone": 20,
    "credit_card": 40,
    "ssn": 40,
    "aadhaar": 40,
    "ip_address": 10,
    "password": 35,
    "api_key": 35,
    "address": 15,
    "names": 10,
    "organizations": 5,
    "locations": 5,
}

# If 2+ of these "identity-linking" categories appear together in the
# same input, add a flat bonus — a name next to a phone number is more
# dangerous than the two found in unrelated documents.
LINKING_CATEGORIES = {"names", "email", "phone", "address", "ssn", "aadhaar"}
COMBO_BONUS = 20

# If the BERT contextual classifier (detectors/deep_learning.py) flags
# text as "sensitive", add up to this many points, scaled by its
# confidence. This matters most for catching leaks that rule-based
# regex and spaCy NER miss entirely (e.g. spelled-out numbers,
# lowercase casual names) - exactly the gap the SRS's NLP layer is
# meant to close.
BERT_MAX_BONUS = 30

HIGH_THRESHOLD = 80
MEDIUM_THRESHOLD = 40


def calculate_risk(findings: dict, dl_result: dict = None) -> dict:
    """
    findings: dict mapping category name -> list of matches
              (combined output from rule_based + nlp_contextual detectors)
    dl_result: optional {"label": str, "confidence": float} from
               detectors/deep_learning.py (BERT classifier)

    Returns: {"score": int, "risk_level": str, "breakdown": dict}
    """
    breakdown = {}
    score = 0

    for category, matches in findings.items():
        count = len(matches) if matches else 0
        if count == 0:
            continue
        weight = CATEGORY_WEIGHTS.get(category, 5)
        contribution = count * weight
        breakdown[category] = contribution
        score += contribution

    linking_hits = [
        cat for cat in LINKING_CATEGORIES
        if findings.get(cat)
    ]
    if len(linking_hits) >= 2:
        score += COMBO_BONUS
        breakdown["combo_bonus"] = COMBO_BONUS

    if dl_result and dl_result.get("label") == "sensitive":
        bert_contribution = round(BERT_MAX_BONUS * dl_result.get("confidence", 0))
        if bert_contribution > 0:
            score += bert_contribution
            breakdown["bert_contextual"] = bert_contribution

    if score > HIGH_THRESHOLD:
        level = "HIGH"
    elif score > MEDIUM_THRESHOLD:
        level = "MEDIUM"
    else:
        level = "LOW"

    return {"score": score, "risk_level": level, "breakdown": breakdown}


if __name__ == "__main__":
    sample_findings = {
        "email": ["john.doe@gmail.com"],
        "phone": ["987-654-3210"],
        "names": ["John Doe"],
        "credit_card": [],
        "password": [],
    }
    from pprint import pprint
    pprint(calculate_risk(sample_findings))
