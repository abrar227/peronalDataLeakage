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
    return list(dict.fromkeys(items))


def extract_entities(text: str) -> dict:
    """
    Returns dict with keys: names, organizations, locations.
    Each value is a de-duplicated list of matched entity strings.
    """
    doc = _nlp(text)

    names, orgs, locations = [], [], []
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            names.append(ent.text)
        elif ent.label_ == "ORG":
            orgs.append(ent.text)
        elif ent.label_ == "GPE":
            locations.append(ent.text)

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
