const dropZone = document.getElementById("drop-zone");
const fileInput = document.getElementById("file-input");
const textInput = document.getElementById("text-input");
const resultBox = document.getElementById("resultBox");
const loading = document.getElementById("loading");
const riskEl = document.getElementById("risk");
const entitiesEl = document.getElementById("entities");
const highlightedTextEl = document.getElementById("highlightedText");
const emailCountEl = document.getElementById("email-count");
const phoneCountEl = document.getElementById("phone-count");

dropZone.onclick = () => fileInput.click();

fileInput.onchange = () => {
    if (fileInput.files[0]) uploadFile(fileInput.files[0]);
};

function scanText() {
    const text = textInput.value.trim();
    if (!text) return alert("Enter text");

    showLoading();

    fetch("/scan", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({text})
    })
    .then(res => res.json())
    .then(displayResult)
    .catch(err => alert(err));
}

function uploadFile(file) {
    const formData = new FormData();
    formData.append("file", file);

    showLoading();

    fetch("/upload", {
        method: "POST",
        body: formData
    })
    .then(res => res.json())
    .then(displayResult)
    .catch(err => alert(err));
}

function showLoading() {
    loading.classList.remove("hidden");
    resultBox.classList.add("hidden");
}

function displayResult(data) {
    loading.classList.add("hidden");
    resultBox.classList.remove("hidden");

    emailCountEl.innerText = data.email.length;
    phoneCountEl.innerText = data.phone.length;

    riskEl.innerText = data.risk_level;

    // Risk color
    if (data.risk_level === "HIGH") riskEl.style.color = "red";
    else if (data.risk_level === "MEDIUM") riskEl.style.color = "orange";
    else riskEl.style.color = "lightgreen";

    entitiesEl.innerHTML = `
        <p><b>Emails:</b> ${data.email.join(", ") || "None"}</p>
        <p><b>Phones:</b> ${data.phone.join(", ") || "None"}</p>
        <p><b>Names:</b> ${data.names.join(", ") || "None"}</p>
        <p><b>Organizations:</b> ${data.organizations.join(", ") || "None"}</p>
        <p><b>Locations:</b> ${data.locations.join(", ") || "None"}</p>
    `;

    highlightedTextEl.innerHTML = data.highlighted_text;
}