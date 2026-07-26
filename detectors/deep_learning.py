"""
detectors/deep_learning.py

Deep learning contextual classification component (SRS 4.6.4).

Loads the fine-tuned BERT sensitivity classifier trained in Colab
(see colab/bert_finetuning.ipynb) and runs real inference.

Expects the unzipped model at: models/bert_leakage_model/
(config.json, model.safetensors/pytorch_model.bin, tokenizer files)

If the model folder is missing or fails to load, this falls back to
an "unavailable" result instead of crashing the app - so app.py keeps
working even before/without the trained model in place.

NOTE: this currently holds the BERT-based classifier. A separate
LSTM/CNN model (also planned in the SRS) can be added later as an
additional signal, either in this same module or a new one, without
changing app.py's call signature.
"""

import os

MODEL_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "models", "bert_leakage_model"
)

MODEL_LOADED = False
_tokenizer = None
_model = None
_torch = None

LABEL_MAP = {0: "non-sensitive", 1: "sensitive"}


def _try_load_model():
    global MODEL_LOADED, _tokenizer, _model, _torch

    if not os.path.isdir(MODEL_DIR):
        print(f"[deep_learning] Model folder not found at {MODEL_DIR} — "
              f"deep learning detection will report 'unavailable'.")
        return

    try:
        import torch
        from transformers import AutoTokenizer, AutoModelForSequenceClassification

        _torch = torch
        _tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
        _model = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR)
        _model.eval()  # inference mode, not training

        MODEL_LOADED = True
        print(f"[deep_learning] BERT model loaded successfully from {MODEL_DIR}")

    except Exception as e:
        print(f"[deep_learning] Failed to load model: {e} — "
              f"deep learning detection will report 'unavailable'.")
        MODEL_LOADED = False


_try_load_model()


def predict(text: str) -> dict:
    """
    Returns: {"label": str, "confidence": float}
    label is one of: "sensitive", "non-sensitive", "unavailable"
    """
    if not MODEL_LOADED or not text.strip():
        return {"label": "unavailable", "confidence": 0.0}

    try:
        inputs = _tokenizer(
            text, return_tensors="pt", truncation=True, padding=True, max_length=128
        )
        with _torch.no_grad():
            outputs = _model(**inputs)

        probs = _torch.softmax(outputs.logits, dim=1)[0]
        pred_id = int(_torch.argmax(probs))
        confidence = float(probs[pred_id])

        return {"label": LABEL_MAP.get(pred_id, "unavailable"), "confidence": round(confidence, 4)}

    except Exception as e:
        print(f"[deep_learning] Inference error: {e}")
        return {"label": "unavailable", "confidence": 0.0}


if __name__ == "__main__":
    test_sentences = [
        "his number is like nine eight seven six five four three two one zero",
        "the weather today is sunny with a high of 28 degrees",
        "my password is still just doby123, never changed it",
        "our office is closed on public holidays",
    ]
    for s in test_sentences:
        print(predict(s), "-", s)
