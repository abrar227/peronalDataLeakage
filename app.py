from flask import Flask, render_template, request, jsonify
import re
import spacy
import html
from PyPDF2 import PdfReader

# Load spaCy model safely
try:
    nlp = spacy.load("en_core_web_sm")
except:
    import os
    os.system("python -m spacy download en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

app = Flask(__name__)

# Limit upload size (10MB)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024


# ---------- UTIL FUNCTIONS ----------

def unique(items):
    return list(dict.fromkeys(items))


def extract_text_from_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text


def calculate_risk(data):
    score = 0

    score += len(data["email"]) * 25
    score += len(data["phone"]) * 30
    score += len(data["names"]) * 10
    score += len(data["organizations"]) * 5
    score += len(data["locations"]) * 5

    if score > 80:
        return "HIGH"
    elif score > 40:
        return "MEDIUM"
    else:
        return "LOW"


# ---------- CORE DETECTION ----------

def detect_data(text):
    doc = nlp(text)

    # Improved regex
    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-z]{2,}', text)
    phones = re.findall(r'\b\+?\d{1,3}?[-.\s]?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b', text)

    names, orgs, locations = [], [], []

    for ent in doc.ents:
        if ent.label_ == "PERSON":
            names.append(ent.text)
        elif ent.label_ == "ORG":
            orgs.append(ent.text)
        elif ent.label_ == "GPE":
            locations.append(ent.text)

    result = {
        "email": unique(emails),
        "phone": unique(phones),
        "names": unique(names),
        "organizations": unique(orgs),
        "locations": unique(locations)
    }

    result["risk_level"] = calculate_risk(result)
    return result


# ---------- HIGHLIGHT ----------

def highlight_text(text, data):
    text = html.escape(text)

    # Email & phone
    text = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-z]{2,}',
                  r'<span class="email">\g<0></span>', text)

    text = re.sub(r'\b\+?\d{1,3}?[-.\s]?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',
                  r'<span class="phone">\g<0></span>', text)

    # Entities
    for name in data["names"]:
        text = text.replace(name, f'<span class="name">{name}</span>')

    for org in data["organizations"]:
        text = text.replace(org, f'<span class="org">{org}</span>')

    for loc in data["locations"]:
        text = text.replace(loc, f'<span class="location">{loc}</span>')

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

    result = detect_data(text)
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

    result = detect_data(text)
    result["highlighted_text"] = highlight_text(text, result)

    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True)