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
MIN_HISTORY_FOR_BASELINE = 5    # need at least 5 past scans to trust a personal baseline
ZSCORE_THRESHOLD = 2.0          # std-dev threshold for personal baseline anomaly
HUGE_TEXT_THRESHOLD = 800       # submissions at or above this char length are flagged as volume anomalies
HIGH_RISK_THRESHOLD = 70        # submissions at or above this risk score are flagged as high risk


def _generate_synthetic_training_data(n_normal=300, n_anomalies=30, seed=42):
    """
    Builds a synthetic behavioral dataset to train the GLOBAL fallback model on:
      - "Normal" activity: business hours (9am-7pm), short-to-medium
        text length (10-500 chars), low-to-moderate risk scores (0-30).
      - Injected anomalies across distinct behavioral dimensions:
        1. Volume anomalies (huge text during business hours)
        2. Risk anomalies (high risk score during business hours)
        3. Off-hours anomalies (unusual hours 11pm-5am)
    """
    rng = np.random.default_rng(seed)

    # 1. Normal usage
    normal_hours = rng.integers(9, 19, size=n_normal)          # 9am-6pm
    normal_length = rng.normal(150, 60, size=n_normal).clip(10, 500)
    normal_risk = rng.normal(10, 8, size=n_normal).clip(0, 30)
    normal = np.column_stack([normal_hours, normal_length, normal_risk])

    # 2. Volume anomalies: large text during business hours with normal risk
    n_vol = n_anomalies // 3
    vol_hours = rng.integers(9, 19, size=n_vol)
    vol_length = rng.normal(2500, 800, size=n_vol).clip(800, 6000)
    vol_risk = rng.normal(10, 8, size=n_vol).clip(0, 30)
    vol_anomalies = np.column_stack([vol_hours, vol_length, vol_risk])

    # 3. Risk anomalies: sensitive submissions during business hours with normal length
    n_risk = n_anomalies // 3
    risk_hours = rng.integers(9, 19, size=n_risk)
    risk_length = rng.normal(150, 60, size=n_risk).clip(10, 500)
    risk_score = rng.normal(85, 10, size=n_risk).clip(70, 100)
    risk_anomalies = np.column_stack([risk_hours, risk_length, risk_score])

    # 4. Off-hours anomalies: night submissions
    n_off = n_anomalies - n_vol - n_risk
    off_hours = rng.choice([0, 1, 2, 3, 4, 5, 22, 23], size=n_off)
    off_length = rng.normal(1500, 600, size=n_off).clip(200, 5000)
    off_risk = rng.normal(50, 25, size=n_off).clip(10, 100)
    off_anomalies = np.column_stack([off_hours, off_length, off_risk])

    anomalies = np.vstack([vol_anomalies, risk_anomalies, off_anomalies])
    data = np.vstack([normal, anomalies])
    return data


def _train_model():
    global MODEL_LOADED, _model
    try:
        training_data = _generate_synthetic_training_data()
        # contamination = expected proportion of anomalies in training data
        _model = IsolationForest(contamination=0.08, random_state=42)
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


def get_user_scan_count(user_id: str) -> dict:
    """Returns the number of scans logged for this user and whether their baseline is active."""
    history = _get_user_history(user_id)
    return {
        "scan_count": len(history),
        "baseline_required": MIN_HISTORY_FOR_BASELINE,
        "has_baseline": len(history) >= MIN_HISTORY_FOR_BASELINE,
    }


def _check_against_user_baseline(history, text_length, risk_score):
    """
    Compares the new scan to this specific user's own past average,
    using a z-score and domain sensitivity shift rules.

    Returns: {"is_anomaly": bool, "reason": str, ...} or None if not enough
    history to trust a personal baseline yet.
    """
    if len(history) < MIN_HISTORY_FOR_BASELINE:
        return None

    lengths = np.array([h["text_length"] for h in history])
    risks = np.array([h["risk_score"] for h in history])

    length_mean, length_std = lengths.mean(), lengths.std()
    risk_mean, risk_std = risks.mean(), risks.std()

    # Prevent zero or near-zero variance from blowing up z-scores on minor differences
    eff_length_std = max(float(length_std), 40.0)
    eff_risk_std = max(float(risk_std), 5.0)

    length_z = (text_length - length_mean) / eff_length_std
    risk_z = (risk_score - risk_mean) / eff_risk_std

    reasons = []

    # 1. Text volume anomaly against user's history
    # Requires statistical deviation with at least 200 chars increase, OR exceeding huge threshold and 1.5x average
    is_length_anomaly = (
        (length_z > ZSCORE_THRESHOLD and (text_length - length_mean) >= 200)
        or (text_length >= HUGE_TEXT_THRESHOLD and text_length >= length_mean * 1.5)
    )
    if is_length_anomaly:
        reasons.append(
            f"text length ({text_length}) is far above this user's usual average ({length_mean:.0f})"
        )

    # 2. Risk score anomaly against user's history
    # Requires statistical deviation with at least 15 risk points increase, OR jump from insensitive baseline to sensitive data
    is_risk_jump = (risk_mean < 20 and risk_score >= 20 and (risk_score - risk_mean) >= 15)
    is_risk_anomaly = (
        (risk_z > ZSCORE_THRESHOLD and (risk_score - risk_mean) >= 15)
        or is_risk_jump
    )
    if is_risk_anomaly:
        reasons.append(
            f"risk score ({risk_score}) is far above this user's usual average ({risk_mean:.0f})"
        )

    is_anomaly = len(reasons) > 0
    reason = "; ".join(reasons) if reasons else f"within this user's normal pattern (baseline: {len(history)} scans)"

    return {
        "is_anomaly": is_anomaly,
        "reason": reason,
        "baseline_count": len(history) + 1,
        "baseline_mean_risk": round(float(risk_mean), 1),
        "baseline_mean_length": round(float(length_mean), 1),
    }


def check_anomaly(user_id: str, event_metadata: dict) -> dict:
    """
    event_metadata expected keys: risk_score (int/float), text_length (int)

    Logic:
      1. If this user has enough history (MIN_HISTORY_FOR_BASELINE scans),
         compare the new scan to THEIR OWN average (per-user baseline).
      2. Otherwise, fall back to the global IsolationForest model supported
         by explicit domain guardrails for huge text and high risk submissions.

    Returns: {"is_anomaly": bool, "reason": str, ...}
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

    # Not enough history yet -> cold start / global fallback
    is_anomaly = False
    reasons = []

    # Guardrail 1: Huge text submission on cold start
    if text_length >= HUGE_TEXT_THRESHOLD:
        is_anomaly = True
        reasons.append(f"unusually large submission ({text_length} chars)")

    # Guardrail 2: High risk score on cold start
    if risk_score >= HIGH_RISK_THRESHOLD:
        is_anomaly = True
        reasons.append(f"unusually high risk score ({risk_score})")

    # Guardrail 3: Off-hours scan
    if hour < 6 or hour > 21:
        is_anomaly = True
        reasons.append(f"unusual scan hour ({hour}:00)")

    # Fallback model prediction
    if MODEL_LOADED:
        try:
            prediction = _model.predict([features])[0]  # -1 = anomaly, 1 = normal
            if prediction == -1:
                is_anomaly = True
                if not reasons:
                    if text_length > 500:
                        reasons.append(f"submission length ({text_length} chars) deviates from typical usage")
                    elif risk_score > 30:
                        reasons.append(f"elevated risk score ({risk_score}) deviates from typical pattern")
                    else:
                        reasons.append("deviates from typical usage pattern (new user, no baseline yet)")
        except Exception as e:
            print(f"[anomaly] Inference error: {e}")

    _log_activity(user_id, features, is_anomaly)

    reason = "; ".join(reasons) if is_anomaly else "within typical usage pattern (new user, no baseline yet)"
    return {
        "is_anomaly": is_anomaly,
        "reason": reason,
        "baseline_count": len(history) + 1,
        "baseline_required": MIN_HISTORY_FOR_BASELINE,
    }


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
