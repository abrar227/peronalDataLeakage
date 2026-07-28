"""
detectors/explainability.py

Explainable AI layer (SRS 4.6.8).

Uses LIME (Local Interpretable Model-agnostic Explanations) to explain
WHY the BERT model (detectors/deep_learning.py) classified a given
piece of text as "sensitive". LIME works by slightly perturbing the
input text (removing/masking words) many times, observing how the
model's prediction changes, and inferring which words pushed the
prediction toward "sensitive" the most.

This directly satisfies the SRS requirement for a human-readable
rationale accompanying each detection decision (not just a raw
label + confidence number).

NOTE ON COST: LIME needs many forward passes through BERT per
explanation (controlled by num_samples below). This is noticeably
slower than a normal prediction - expect a few seconds per call on
CPU. Because of this, app.py only calls this when it's actually
useful: when BERT has flagged the text as "sensitive" in the first
place. There's no point explaining a "non-sensitive" verdict for
this project's purposes.
"""

from detectors import deep_learning

EXPLAINABILITY_AVAILABLE = False
_explainer = None

try:
    from lime.lime_text import LimeTextExplainer
    _explainer = LimeTextExplainer(class_names=["non-sensitive", "sensitive"])
    EXPLAINABILITY_AVAILABLE = True
except ImportError:
    print("[explainability] 'lime' not installed — explanations will be "
          "unavailable. Run: pip install lime")


def _predict_proba(texts):
    """
    LIME needs a function that takes a LIST of text strings and returns
    a numpy array of shape (n_texts, n_classes) with class probabilities.
    This wraps the already-loaded BERT model from deep_learning.py.
    """
    import numpy as np

    if not deep_learning.MODEL_LOADED:
        # Should not normally be reached (checked before calling), but
        # guard anyway so LIME doesn't crash on a missing model.
        return np.array([[0.5, 0.5] for _ in texts])

    tokenizer = deep_learning._tokenizer
    model = deep_learning._model
    torch = deep_learning._torch

    inputs = tokenizer(
        list(texts), return_tensors="pt", truncation=True,
        padding=True, max_length=128
    )
    with torch.no_grad():
        outputs = model(**inputs)
    probs = torch.softmax(outputs.logits, dim=1).numpy()
    return probs


def explain_prediction(text: str, num_features: int = 8, num_samples: int = 200) -> dict:
    """
    Returns a human-readable explanation of the BERT model's decision.

    Returns:
        {
          "available": bool,
          "top_words": [{"word": str, "weight": float}, ...],
          "summary": str
        }
    weight > 0 means that word pushed the prediction TOWARD "sensitive".
    weight < 0 means it pushed away from "sensitive" (toward non-sensitive).
    """
    if not EXPLAINABILITY_AVAILABLE or not deep_learning.MODEL_LOADED:
        return {
            "available": False,
            "top_words": [],
            "summary": "Explanation unavailable (LIME or BERT model not loaded).",
        }

    if not text.strip():
        return {"available": False, "top_words": [], "summary": "No text provided."}

    try:
        explanation = _explainer.explain_instance(
            text,
            _predict_proba,
            num_features=num_features,
            num_samples=num_samples,
            labels=(1,),  # class index 1 = "sensitive"
        )

        word_weights = explanation.as_list(label=1)
        top_words = [
            {"word": w, "weight": round(weight, 4)}
            for w, weight in word_weights
        ]

        contributing = [tw["word"] for tw in top_words if tw["weight"] > 0]
        if contributing:
            summary = (
                "Flagged as sensitive mainly because of: "
                + ", ".join(contributing[:5])
            )
        else:
            summary = "Model flagged this as sensitive, but no single word stood out strongly."

        return {"available": True, "top_words": top_words, "summary": summary}

    except Exception as e:
        print(f"[explainability] Failed to generate explanation: {e}")
        return {
            "available": False,
            "top_words": [],
            "summary": "Explanation generation failed.",
        }


if __name__ == "__main__":
    sample = "my password is still just doby123, never changed it"
    result = explain_prediction(sample)
    print(result)
