"""
detectors/risk_scoring.py

Computes a risk score from combined detector output.
Weighted by category severity, plus a bonus when multiple
categories co-occur (e.g. a name + phone together is riskier
than either alone, since it's more easily linked to a person).

UPDATE (proportional percentage scoring):
  Earlier version added each category's weight once, then flat-capped
  the total at 100. The problem: flat capping loses resolution - a
  text with 3 sensitive categories and a text with 8 sensitive
  categories could both just show "100%", even though the second is
  clearly worse.

  Fixed by computing the maximum score the system could EVER produce
  (every category present + combo bonus + full BERT bonus), then
  expressing the actual score as a percentage OF that theoretical
  maximum. This means:
    - The percentage is always naturally between 0-100 (raw score can
      never exceed the max, since each category only contributes once).
    - Two different "very bad" texts are still distinguished from each
      other, instead of both collapsing to the same capped number.
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

HIGH_THRESHOLD = 70
MEDIUM_THRESHOLD = 25

# The theoretical maximum raw score: every category weight, once each,
# plus the combo bonus, plus the full BERT bonus. Used to normalize
# the raw score into a true 0-100 percentage.
MAX_POSSIBLE_SCORE = sum(CATEGORY_WEIGHTS.values()) + COMBO_BONUS + BERT_MAX_BONUS


def calculate_risk(findings: dict, dl_result: dict = None) -> dict:
    """
    findings: dict mapping category name -> list of matches
              (combined output from rule_based + nlp_contextual detectors)
    dl_result: optional {"label": str, "confidence": float} from
               detectors/deep_learning.py (BERT classifier)

    Returns: {"score": int (0-100, a risk percentage), "risk_level": str, "breakdown": dict}
    """
    breakdown = {}
    raw_score = 0

    for category, matches in findings.items():
        count = len(matches) if matches else 0
        if count == 0:
            continue
        weight = CATEGORY_WEIGHTS.get(category, 5)
        # Weight counts once per category present - a long paragraph
        # repeating the same sensitive item many times should not
        # inflate the score beyond what one instance already implies.
        breakdown[category] = weight
        raw_score += weight

    linking_hits = [
        cat for cat in LINKING_CATEGORIES
        if findings.get(cat)
    ]
    if len(linking_hits) >= 2:
        raw_score += COMBO_BONUS
        breakdown["combo_bonus"] = COMBO_BONUS

    if dl_result and dl_result.get("label") == "sensitive":
        bert_contribution = round(BERT_MAX_BONUS * dl_result.get("confidence", 0))
        if bert_contribution > 0:
            raw_score += bert_contribution
            breakdown["bert_contextual"] = bert_contribution

    # Normalize against the theoretical maximum instead of flat-capping,
    # so the percentage keeps distinguishing "bad" from "very bad".
    score = round((raw_score / MAX_POSSIBLE_SCORE) * 100)
    score = min(score, 100)  # safety net only - shouldn't normally trigger

    if score > HIGH_THRESHOLD:
        level = "HIGH"
    elif score > MEDIUM_THRESHOLD:
        level = "MEDIUM"
    else:
        level = "LOW"

    return {"score": score, "risk_level": level, "breakdown": breakdown}


if __name__ == "__main__":
    from pprint import pprint

    # A "moderately bad" example (3 categories)
    moderate_findings = {
        "email": ["john.doe@gmail.com"],
        "phone": ["987-654-3210"],
        "names": ["John Doe"],
    }
    print("Moderate case:")
    pprint(calculate_risk(moderate_findings))

    # A "very bad" example (many categories) - should score noticeably
    # higher than the moderate case, not collapse to the same number.
    severe_findings = {
        "email": ["john.doe@gmail.com"],
        "phone": ["987-654-3210"],
        "ssn": ["123-45-6789"],
        "credit_card": ["4111 1111 1111 1111"],
        "password": ["Summer2024!"],
        "address": ["42 Lakeview Street"],
        "names": ["John Doe"],
    }
    print("\nSevere case:")
    pprint(calculate_risk(severe_findings, {"label": "sensitive", "confidence": 0.95}))
