from flask import Flask, render_template, request, jsonify
import re
import json

app = Flask(__name__)

def detect_data(text):
    emails = re.findall(r'\S+@\S+', text)
    phones = re.findall(r'\d{10}', text)
    return {"email": emails, "phone": phones}

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
    return jsonify(result)

# ✅ MOVE THIS ABOVE app.run
@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("file")

    if not file:
        return jsonify({"error": "No file uploaded"})

    content = file.read().decode("utf-8")
    result = detect_data(content)
    return jsonify(result)

# ✅ ALWAYS KEEP THIS LAST
if __name__ == "__main__":
    app.run(debug=True)