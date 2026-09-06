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

UPDATE (per-user baseline):
  A single global "normal" doesn't work well - a user who always
  handles a lot of sensitive data would get flagged every time,
  even though that IS normal for them. So now, if a user has
  enough history, we compare their new scan to THEIR OWN past
  average instead of everyone else's average. If they don't have
  enough history yet, we fall back to the old global model.

DATA:
  Since this project has no real multi-week user history, the
  global model is trained on a SYNTHETIC baseline of normal
  behavior (see _generate_synthetic_training_data below), with a
  few synthetic anomalies mixed in so the model has something to
  contrast against. This is a standard, legitimate approach for
  demonstrating the mechanism in an academic project - a real
  deployment would retrain this periodically on actual logged
  activity (see logs/activity_log.csv, which this module appends
  to every time check_anomaly is called, for that future use).
  The per-user baseline, on the other hand, is calculated directly
  from that same real logged activity - no synthetic data involved.

MODEL:
  scikit-learn's IsolationForest - an unsupervised model that
  learns what combinations of behavior look "normal" and isolates
  points that don't fit, without needing labelled anomaly examples.
  Used only as the fallback for users with little/no history.
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

# --- Per-user baseline settings ---
MIN_HISTORY_FOR_BASELINE = 10   # need at least this many past scans to trust a personal baseline
ZSCORE_THRESHOLD = 3.0          # how many std-devs away counts as "way more than usual"


def _generate_synthetic_training_data(n_normal=300, n_anomalies=15, seed=42):
    """
    Builds a synthetic behavioral dataset to train the GLOBAL fallback model on:
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
        print("[anomaly] IsolationForest trained on synthetic behavioral baseline (fallback model).")
    except Exception as e:
        print(f"[anomaly] Failed to train model: {e}")
        MODEL_LOADED = False


_train_model()


def _log_activity(user_id, features, is_anomaly):
    """Appends this event to a local CSV log for future retraining / per-user baselines."""
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    file_exists = os.path.isfile(LOG_PATH)

    with open(LOG_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "user_id"] + FEATURE_NAMES + ["is_anomaly"])
        writer.writerow(
            [datetime.now().isoformat(), user_id] + features + [is_anomaly]
        )


def _get_user_history(user_id):
    """Reads this user's past scans from the log file (excludes today's current one)."""
    history = []

    if not os.path.isfile(LOG_PATH):
        return history

    with open(LOG_PATH, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["user_id"] == user_id:
                history.append({
                    "text_length": float(row["text_length"]),
                    "risk_score": float(row["risk_score"]),
                })

    return history


def _check_against_user_baseline(history, text_length, risk_score):
    """
    Compares the new scan to this specific user's own past average,
    using a z-score (how many standard deviations away from their
    own normal this new value is).

    Returns: {"is_anomaly": bool, "reason": str} or None if not enough
    history to trust a personal baseline yet.
    """
    if len(history) < MIN_HISTORY_FOR_BASELINE:
        return None

    lengths = np.array([h["text_length"] for h in history])
    risks = np.array([h["risk_score"] for h in history])

    length_mean, length_std = lengths.mean(), lengths.std()
    risk_mean, risk_std = risks.mean(), risks.std()

    # avoid divide-by-zero if a user's history has no variation at all
    length_std = length_std if length_std > 0 else 1e-6
    risk_std = risk_std if risk_std > 0 else 1e-6

    length_z = (text_length - length_mean) / length_std
    risk_z = (risk_score - risk_mean) / risk_std

    reasons = []
    if length_z > ZSCORE_THRESHOLD:
        reasons.append(
            f"text length ({text_length}) is far above this user's usual average ({length_mean:.0f})"
        )
    if risk_z > ZSCORE_THRESHOLD:
        reasons.append(
            f"risk score ({risk_score}) is far above this user's usual average ({risk_mean:.0f})"
        )

    is_anomaly = len(reasons) > 0
    reason = "; ".join(reasons) if reasons else "within this user's normal pattern"

    return {"is_anomaly": is_anomaly, "reason": reason}


def check_anomaly(user_id: str, event_metadata: dict) -> dict:
    """
    event_metadata expected keys: risk_score (int/float), text_length (int)

    Logic:
      1. If this user has enough history (MIN_HISTORY_FOR_BASELINE scans),
         compare the new scan to THEIR OWN average (per-user baseline).
      2. Otherwise, fall back to the global IsolationForest model trained
         on synthetic "typical" behavior.

    Returns: {"is_anomaly": bool, "reason": str}
    """
    now = datetime.now()
    hour = now.hour
    text_length = event_metadata.get("text_length", 0)
    risk_score = event_metadata.get("risk_score", 0)
    features = [hour, text_length, risk_score]

    history = _get_user_history(user_id)
    result = _check_against_user_baseline(history, text_length, risk_score)

    if result is not None:
        # Used the per-user baseline path
        _log_activity(user_id, features, result["is_anomaly"])
        return result

    # Not enough history yet -> fall back to global model
    if not MODEL_LOADED:
        _log_activity(user_id, features, False)
        return {"is_anomaly": False, "reason": "anomaly model not available, and not enough user history yet"}

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
            reason = "; ".join(reasons) if reasons else "deviates from typical usage pattern (new user, no baseline yet)"
            return {"is_anomaly": True, "reason": reason}

        return {"is_anomaly": False, "reason": "within typical usage pattern (new user, no baseline yet)"}

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
