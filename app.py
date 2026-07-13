from flask import Flask, render_template, request, jsonify
import re
import json
import spacy
from PyPDF2 import PdfReader

nlp = spacy.load("en_core_web_sm")

app = Flask(__name__)

def extract_text_from_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

def calculate_risk(data):
    score = 0

    score += len(data["email"]) * 2
    score += len(data["phone"]) * 2
    score += len(data["names"]) * 1

    if score > 10:
        return "HIGH"
    elif score > 5:
        return "MEDIUM"
    else:
        return "LOW"

def detect_data(text):
    doc = nlp(text)

    emails = re.findall(r'\S+@\S+', text)
    phones = re.findall(r'\+?\d[\d\s-]{8,}\d', text)

    names = []
    orgs = []
    locations = []

    for ent in doc.ents:
        if ent.label_ == "PERSON":
            names.append(ent.text)
        elif ent.label_ == "ORG":
            orgs.append(ent.text)
        elif ent.label_ == "GPE":
            locations.append(ent.text)

    result = {
        "email": list(set(emails)),
        "phone": list(set(phones)),
        "names": list(set(names)),
        "organizations": list(set(orgs)),
        "locations": list(set(locations))
    }

    # ✅ ADD THIS LINE
    result["risk_level"] = calculate_risk(result)

    return result
def highlight_text(text):
    text = re.sub(r'\S+@\S+', r'<span class="highlight-email">\g<0></span>', text)
    text = re.sub(r'\+?\d[\d\s-]{8,}\d', r'<span class="highlight-phone">\g<0></span>', text)
    return text
@app.route("/", methods=["GET", "POST"])
def home():
    result = None
    if request.method == "POST":
        text = request.form["text"]
        result = detect_data(text)

    return render_template("index.html", result=json.dumps(result, indent=2))

@app.route("/detect", methods=["POST"])
def detect():
    data = request.get_json()
    text = data.get("text", "")

    result = detect_data(text)

    # ✅ ADD THIS LINE
    result["highlighted_text"] = highlight_text(text)

    return jsonify(result)
# ✅ MOVE THIS ABOVE app.run
@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']

    if file.filename.endswith('.pdf'):
        text = extract_text_from_pdf(file)
    else:
        text = file.read().decode('utf-8')

    result = detect_data(text)

    # ✅ ADD THIS LINE
    result["highlighted_text"] = highlight_text(text)

    return jsonify({'result': result})
# ✅ ALWAYS KEEP THIS LAST
if __name__ == "__main__":
    app.run(debug=True)
