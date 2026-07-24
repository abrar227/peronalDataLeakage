"""
detectors/deep_learning.py

Deep learning (LSTM/CNN) pattern detection component (SRS 4.6.4).

NOT YET IMPLEMENTED. This is a stub so app.py can call it safely
before the model exists — it returns an empty/neutral result instead
of crashing or being skipped silently.

PLAN:
  1. Once data/train.csv has a few hundred+ labelled rows, train an
     LSTM or CNN text classifier in Google Colab (GPU).
  2. Export weights (e.g. model.pt) and a tokenizer/vocab file.
  3. Load them here at module import time, replace predict() below
     with real inference.
  4. Keep the same return shape so risk_scoring.py and app.py don't
     need to change.
"""

MODEL_LOADED = False
# TODO: load trained model + tokenizer here once available, e.g.
# import torch
# model = torch.load("models/lstm_classifier.pt")
# MODEL_LOADED = True


def predict(text: str) -> dict:
    """
    Returns: {"label": str, "confidence": float}
    label is one of: "sensitive", "non-sensitive", "unavailable"
    """
    if not MODEL_LOADED:
        return {"label": "unavailable", "confidence": 0.0}

    # TODO: replace with real model inference
    # tokens = tokenizer(text)
    # output = model(tokens)
    # return {"label": output.label, "confidence": output.confidence}
    return {"label": "unavailable", "confidence": 0.0}


if __name__ == "__main__":
    print(predict("sample text"))
