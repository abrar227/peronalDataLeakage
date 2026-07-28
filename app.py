from flask import Flask, render_template, request, jsonify
import html
from PyPDF2 import PdfReader

from detectors import rule_based, nlp_contextual, deep_learning, anomaly, explainability
from detectors.risk_scoring import calculate_risk

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10MB


# ---------- UTIL ----------

def extract_text_from_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text


def run_all_detectors(text: str, user_id: str = "demo_user") -> dict:
    """
    Runs rule-based + NLP detectors, combines findings, calls the BERT
    contextual classifier, computes a risk score, and checks whether
    this submission's behavior (text volume, time of day, resulting
    risk score) looks anomalous compared to normal usage patterns.
    """
    pattern_findings = rule_based.detect_patterns(text)
    entity_findings = nlp_contextual.extract_entities(text)

    combined = {**pattern_findings, **entity_findings}

    dl_result = deep_learning.predict(text)
    risk = calculate_risk(combined, dl_result)

    # Only run LIME explanation when it's actually useful - i.e. when
    # BERT flagged this as sensitive. LIME needs many forward passes
    # through BERT, so skip it entirely for non-sensitive verdicts to
    # keep the app responsive.
    if dl_result.get("label") == "sensitive":
        explanation = explainability.explain_prediction(text)
    else:
        explanation = {"available": False, "top_words": [], "summary": "Not applicable — text not flagged as sensitive."}

    anomaly_result = anomaly.check_anomaly(
        user_id,
        {"risk_score": risk["score"], "text_length": len(text)},
    )

    return {
        "email": combined.get("email", []),
        "phone": combined.get("phone", []),
        "credit_card": combined.get("credit_card", []),
        "ssn": combined.get("ssn", []),
        "aadhaar": combined.get("aadhaar", []),
        "ip_address": combined.get("ip_address", []),
        "password": combined.get("password", []),
        "api_key": combined.get("api_key", []),
        "address": combined.get("address", []),
        "names": combined.get("names", []),
        "organizations": combined.get("organizations", []),
        "locations": combined.get("locations", []),
        "deep_learning": dl_result,
        "explanation": explanation,
        "anomaly": anomaly_result,
        "risk_score": risk["score"],
        "risk_level": risk["risk_level"],
        "risk_breakdown": risk["breakdown"],
    }


CATEGORY_CSS = {
    "email": "email",
    "phone": "phone",
    "credit_card": "credit-card",
    "ssn": "ssn",
    "aadhaar": "aadhaar",
    "ip_address": "ip-address",
    "password": "password",
    "api_key": "api-key",
    "address": "address",
    "names": "name",
    "organizations": "org",
    "locations": "location",
}


def highlight_text(text: str, findings: dict) -> str:
    """
    Wraps every detected match (from any category) in a <span> with a
    category-specific CSS class, driven directly by the already-computed
    findings dict (not by re-running regex), so what gets highlighted is
    guaranteed to match what was actually detected/reported.
    """
    text = html.escape(text)

    # Collect (match_string, css_class) pairs, longest match first, so a
    # longer match (e.g. a full address) gets wrapped before a shorter
    # one nested inside it (e.g. a house number) can interfere.
    all_matches = []
    for category, css_class in CATEGORY_CSS.items():
        for match in findings.get(category, []):
            escaped = html.escape(match)
            if escaped:
                all_matches.append((escaped, css_class))

    all_matches.sort(key=lambda pair: len(pair[0]), reverse=True)

    for escaped_match, css_class in all_matches:
        if escaped_match in text:
            text = text.replace(
                escaped_match,
                f'<span class="{css_class}">{escaped_match}</span>',
                1,
            )

    return text


# ---------- ROUTES ----------

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/scan", methods=["POST"])
def scan():
    data = request.get_json(silent=True) or {}
    text = data.get("text", "").strip()

    if not text:
        return jsonify({"error": "No text provided"}), 400

    result = run_all_detectors(text)
    result["highlighted_text"] = highlight_text(text, result)
    return jsonify(result)


@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files or request.files["file"].filename == "":
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]

    try:
        if file.filename.lower().endswith(".pdf"):
            text = extract_text_from_pdf(file)
        else:
            text = file.read().decode("utf-8", errors="replace")
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    result = run_all_detectors(text)
    result["highlighted_text"] = highlight_text(text, result)
    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True)
