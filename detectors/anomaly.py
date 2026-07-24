"""
detectors/anomaly.py

Anomaly detection for insider threats (SRS 4.6.5).

NOT YET IMPLEMENTED. Unlike the other detectors, this one needs
BEHAVIORAL data (who accessed/sent what, how often, at what times) —
not just the text content of a single scan. That means it needs a
separate data pipeline (access logs) before it can do anything real.

PLAN:
  1. Decide what behavioral signal you'll log per scan/user, e.g.:
     - user_id, timestamp, file/text size, risk_score from this scan
  2. Accumulate these into a log (CSV or small local DB) as the app
     is used.
  3. Once you have enough logged activity, use scikit-learn
     (e.g. IsolationForest or a simple z-score on frequency/volume)
     to flag sessions that deviate from a user's normal pattern.
  4. Keep the same return shape so app.py doesn't need to change.
"""

MODEL_LOADED = False


def check_anomaly(user_id: str, event_metadata: dict) -> dict:
    """
    Returns: {"is_anomaly": bool, "reason": str}

    event_metadata example: {"risk_score": 65, "text_length": 240,
                              "timestamp": "2026-07-24T10:32:00"}
    """
    if not MODEL_LOADED:
        return {"is_anomaly": False, "reason": "anomaly detection not yet trained"}

    # TODO: replace with real scikit-learn model inference
    return {"is_anomaly": False, "reason": "anomaly detection not yet trained"}


if __name__ == "__main__":
    print(check_anomaly("test_user", {"risk_score": 65, "text_length": 240}))
