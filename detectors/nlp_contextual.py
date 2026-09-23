"""
detectors/nlp_contextual.py

NLP-based contextual analysis component (SRS 4.6.3).

Supports two spaCy models, switchable via the SPACY_MODEL environment
variable:

  - "en_core_web_sm"  (default) — fast, lightweight, CPU-friendly.
  - "en_core_web_trf" — transformer-based (RoBERTa-backed), stronger
    contextual understanding, noticeably slower on CPU. This is the
    "explore before committing to full BERT fine-tuning" step.

If the requested model isn't installed, this falls back to
en_core_web_sm automatically and prints a warning, so the app never
crashes just because trf isn't set up yet.

TODO (next milestone, after dataset has a few hundred+ rows):
  - Fine-tune / use a BERT-based text classifier (via Hugging Face
    Transformers) trained on data/train.csv to output a sensitivity
    label + confidence score for a given passage, not just entities.
  - Swap this module's implementation, keep the same function
    signature (extract_entities) so app.py doesn't need to change.
"""

import os
import re
import spacy

MODEL_NAME = os.environ.get("SPACY_MODEL", "en_core_web_sm")


def _load_model(name: str):
    try:
        return spacy.load(name)
    except OSError:
        if name != "en_core_web_sm":
            print(
                f"[nlp_contextual] '{name}' not installed — "
                f"falling back to en_core_web_sm. "
                f"Run: python -m spacy download {name}"
            )
            return _load_model("en_core_web_sm")
        # even the small default model is missing - download it
        import subprocess
        subprocess.run(["python", "-m", "spacy", "download", name], check=True)
        return spacy.load(name)


_nlp = _load_model(MODEL_NAME)
ACTIVE_MODEL = _nlp.meta.get("name", MODEL_NAME)


def _unique(items):
    seen = {}
    for value, confidence in items:
        if value not in seen:
            seen[value] = {"value": value, "confidence": confidence}
    return list(seen.values())


# ---------- Self-introduction rule (catches names spaCy's NER misses) ----------
#
# spaCy's PERSON detection relies heavily on capitalization + training-data
# familiarity with the name. A message like "my name is amju" (lowercase,
# uncommon name) often gets missed entirely, even though it's an explicit,
# unambiguous self-identification. This regex layer catches specific,
# low-ambiguity introduction phrasings directly, independent of casing.
#
# Deliberately NOT matching generic "I am X" - that pattern is far too
# prone to false positives ("I am tired", "I am here", "I am going") to
# be worth the noise. Only phrasings that are near-exclusively used for
# naming oneself are included.
#
# Captures up to two words (first + last name) after the trigger phrase.
_NAME_CAPTURE = r"([A-Za-z][A-Za-z'\-]{1,30}(?:\s+[A-Za-z][A-Za-z'\-]{1,30})?)"

# Used only for the "this is X" pattern below, which is the most
# ambiguous trigger phrase ("this is important", "this is fine", etc.
# are far more common than genuine self-intros). Requiring the captured
# word to start uppercase filters almost all of that noise out, since
# real self-intros via "this is X" are virtually always capitalized
# names in practice - unlike "my name is X", which we deliberately keep
# case-insensitive to catch lowercase/casual self-declarations.
_NAME_CAPTURE_CAP = r"([A-Z][A-Za-z'\-]{1,30}(?:\s+[A-Za-z][A-Za-z'\-]{1,30})?)"

SELF_INTRO_PATTERNS = [
    (re.compile(rf"(?i)\bmy name(?:'s| is)\s+{_NAME_CAPTURE}"), 0.85),
    (re.compile(rf"(?i)\byou can call me\s+{_NAME_CAPTURE}"), 0.85),
    (re.compile(rf"(?i)\bi am called\s+{_NAME_CAPTURE}"), 0.8),
    (re.compile(rf"(?i)\bi'?m\s+{_NAME_CAPTURE}\s*,\s*(?:by the way|btw)\b"), 0.75),
    # "this is X" only counts near email/call-style self-intros (e.g.
    # "Hi, this is Karthik from finance"), not generic "this is important" -
    # the lookahead requires a comma/period or a typical intro follow-up
    # word, AND (via _NAME_CAPTURE_CAP) that X starts capitalized.
    (re.compile(rf"(?i:this is)\s+{_NAME_CAPTURE_CAP}(?=[,.]|\s+(?:from|here|speaking|writing))"), 0.6),
]

# Words that can slip through the patterns above but are clearly not names
# (e.g. "my name is not important" -> would otherwise capture "not").
_NAME_STOPWORDS = {
    "not", "just", "also", "very", "really", "here", "there", "happy",
    "sorry", "sure", "fine", "okay", "ok", "good", "great", "done",
    "ready", "going", "trying", "looking", "working", "talking",
    "calling", "writing", "speaking", "from", "the", "a", "an", "still",
    "actually", "literally", "basically",
}


def _extract_self_introduced_names(text: str):
    """Returns a list of (name, confidence) tuples caught by the self-intro patterns."""
    found = []
    for pattern, confidence in SELF_INTRO_PATTERNS:
        for m in pattern.finditer(text):
            name = m.group(1).strip()
            first_word = name.split()[0].lower()
            if first_word in _NAME_STOPWORDS:
                continue
            found.append((name, confidence))
    return found


def _entity_confidence(ent) -> float:
    """
    spaCy's standard NER pipelines (sm or trf) don't expose calibrated
    per-entity probabilities, so this is a heuristic estimate rather
    than a true model confidence:
      - trf (transformer-backed) gets a higher base than sm, since it
        has noticeably stronger contextual understanding.
      - very short entities (1-2 chars) are penalized - they're the
        most likely to be a stray capitalized word, not a real entity.
      - multi-word entities (e.g. "John Doe", "Acme Corp") get a small
        boost - they're less likely to be a false positive than a
        single bare token.
    """
    base = 0.85 if "trf" in ACTIVE_MODEL else 0.7

    text = ent.text.strip()
    if len(text) <= 2:
        base -= 0.25
    elif len(text) <= 4:
        base -= 0.1
    if " " in text:
        base += 0.05

    return round(max(0.3, min(0.95, base)), 2)


def extract_entities(text: str) -> dict:
    """
    Returns dict with keys: names, organizations, locations.
    Each value is a de-duplicated list of {"value": str, "confidence": float}.
    """
    doc = _nlp(text)

    names, orgs, locations = [], [], []
    for ent in doc.ents:
        conf = _entity_confidence(ent)
        if ent.label_ == "PERSON":
            names.append((ent.text, conf))
        elif ent.label_ == "ORG":
            orgs.append((ent.text, conf))
        elif ent.label_ in ("GPE", "LOC", "FAC"):
            locations.append((ent.text, conf))

    # Self-introduction rule runs independently of spaCy and is merged in -
    # it catches explicit name declarations (e.g. lowercase/uncommon names)
    # that the statistical NER model misses.
    names.extend(_extract_self_introduced_names(text))

    return {
        "names": _unique(names),
        "organizations": _unique(orgs),
        "locations": _unique(locations),
    }


if __name__ == "__main__":
    print(f"Active model: {MODEL_NAME}")
    sample = (
        "John Doe works at Google in New York. "
        "He mentioned to a colleague, off the record, that his manager "
        "Sarah Lee was recently let go from Acme Corp."
    )
    from pprint import pprint
    pprint(extract_entities(sample))
