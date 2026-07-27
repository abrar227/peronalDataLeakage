"""
detectors/anomaly.py

Anomaly detection for insider threats (SRS 4.6.5).

LOGIC:
  Rather than inspecting text content, this looks at BEHAVIOR:
  what hour someone is scanning at, how much text/data they're
  submitting, and how sensitive (risk_score) their submissions
  tend to be. A scan that looks very different from "normal"
  usage patterns gets flagged as a potential insider-threat signal
  for human review - it does NOT mean malicious intent for certain,
  only that it deviates from the norm and deserves a second look.

DATA:
  Since this project has no real multi-week user history, the
  model is trained on a SYNTHETIC baseline of normal behavior
  (see _generate_synthetic_training_data below), with a few
  synthetic anomalies mixed in so the model has something to
  contrast against. This is a standard, legitimate approach for
  demonstrating the mechanism in an academic project - a real
  deployment would retrain this periodically on actual logged
  activity (see logs/activity_log.csv, which this module appends
  to every time check_anomaly is called, for that future use).

MODEL:
  scikit-learn's IsolationForest - an unsupervised model that
  learns what combinations of behavior look "normal" and isolates
  points that don't fit, without needing labelled anomaly examples.
"""

import os
import csv
from datetime import datetime

import numpy as np
from sklearn.ensemble import IsolationForest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_PATH = os.path.join(PROJECT_ROOT, "logs", "activity_log.csv")

MODEL_LOADED = False
_model = None

FEATURE_NAMES = ["hour_of_day", "text_length", "risk_score"]


def _generate_synthetic_training_data(n_normal=300, n_anomalies=15, seed=42):
    """
    Builds a synthetic behavioral dataset to train on:
      - "Normal" activity: business hours (9am-7pm), short-to-medium
        text length, low-to-moderate risk scores.
      - Injected anomalies: odd hours (e.g. 2-4am), very large text
        volume, or unusually high risk scores - simulating things
        like bulk data exfiltration or off-hours access.
    """
    rng = np.random.default_rng(seed)

    normal_hours = rng.integers(9, 19, size=n_normal)          # 9am-6pm
    normal_length = rng.normal(150, 60, size=n_normal).clip(10, 500)
    normal_risk = rng.normal(20, 12, size=n_normal).clip(0, 60)
    normal = np.column_stack([normal_hours, normal_length, normal_risk])

    anomaly_hours = rng.choice([1, 2, 3, 4, 23], size=n_anomalies)
    anomaly_length = rng.normal(2500, 800, size=n_anomalies).clip(800, 6000)
    anomaly_risk = rng.normal(140, 30, size=n_anomalies).clip(80, 220)
    anomalies = np.column_stack([anomaly_hours, anomaly_length, anomaly_risk])

    data = np.vstack([normal, anomalies])
    return data


def _train_model():
    global MODEL_LOADED, _model
    try:
        training_data = _generate_synthetic_training_data()
        # contamination = expected proportion of anomalies in training data
        _model = IsolationForest(contamination=0.05, random_state=42)
        _model.fit(training_data)
        MODEL_LOADED = True
        print("[anomaly] IsolationForest trained on synthetic behavioral baseline.")
    except Exception as e:
        print(f"[anomaly] Failed to train model: {e}")
        MODEL_LOADED = False


_train_model()


def _log_activity(user_id, features, is_anomaly):
    """Appends this event to a local CSV log for future retraining on real data."""
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    file_exists = os.path.isfile(LOG_PATH)

    with open(LOG_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "user_id"] + FEATURE_NAMES + ["is_anomaly"])
        writer.writerow(
            [datetime.now().isoformat(), user_id] + features + [is_anomaly]
        )


def check_anomaly(user_id: str, event_metadata: dict) -> dict:
    """
    event_metadata expected keys: risk_score (int/float), text_length (int)

    Returns: {"is_anomaly": bool, "reason": str}
    """
    if not MODEL_LOADED:
        return {"is_anomaly": False, "reason": "anomaly model not available"}

    now = datetime.now()
    hour = now.hour
    text_length = event_metadata.get("text_length", 0)
    risk_score = event_metadata.get("risk_score", 0)

    features = [hour, text_length, risk_score]

    try:
        prediction = _model.predict([features])[0]  # -1 = anomaly, 1 = normal
        is_anomaly = prediction == -1

        _log_activity(user_id, features, is_anomaly)

        if is_anomaly:
            reasons = []
            if hour < 6 or hour > 21:
                reasons.append(f"unusual hour ({hour}:00)")
            if text_length > 1000:
                reasons.append(f"unusually large submission ({text_length} chars)")
            if risk_score > 80:
                reasons.append(f"unusually high risk score ({risk_score})")
            reason = "; ".join(reasons) if reasons else "deviates from normal usage pattern"
            return {"is_anomaly": True, "reason": reason}

        return {"is_anomaly": False, "reason": "within normal usage pattern"}

    except Exception as e:
        print(f"[anomaly] Inference error: {e}")
        return {"is_anomaly": False, "reason": "anomaly check failed"}


if __name__ == "__main__":
    print("Testing anomaly detection:\n")

    test_cases = [
        ("normal_user", {"risk_score": 15, "text_length": 120}),
        ("normal_user", {"risk_score": 30, "text_length": 200}),
        ("suspicious_user", {"risk_score": 190, "text_length": 4500}),
    ]

    for user, meta in test_cases:
        result = check_anomaly(user, meta)
        print(f"{user}: {meta} -> {result}")
