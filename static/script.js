const dropZone = document.getElementById("drop-zone");
const fileInput = document.getElementById("file-input");
const textInput = document.getElementById("text-input");
const resultBox = document.getElementById("resultBox");
const loading = document.getElementById("loading");
const riskEl = document.getElementById("risk");
const riskScoreEl = document.getElementById("risk-score");
const entitiesEl = document.getElementById("entities");
const riskBreakdownEl = document.getElementById("riskBreakdown");
const anomalyPanelEl = document.getElementById("anomalyPanel");
const highlightedTextEl = document.getElementById("highlightedText");

// Maps each JSON key from /scan and /upload to its stat-box element id
const COUNT_ELEMENT_IDS = {
    email: "email-count",
    phone: "phone-count",
    credit_card: "credit-card-count",
    ssn: "ssn-count",
    aadhaar: "aadhaar-count",
    ip_address: "ip-address-count",
    password: "password-count",
    api_key: "api-key-count",
    address: "address-count",
    names: "name-count",
    organizations: "org-count",
    locations: "location-count",
};

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

    if (data.error) {
        alert(data.error);
        return;
    }

    resultBox.classList.remove("hidden");

    // Update every stat box count
    for (const [key, elementId] of Object.entries(COUNT_ELEMENT_IDS)) {
        const el = document.getElementById(elementId);
        if (el) {
            const list = data[key] || [];
            el.innerText = list.length;
        }
    }

    // Risk level + score
    riskEl.innerText = data.risk_level || "UNKNOWN";
    riskScoreEl.innerText = data.risk_score !== undefined ? data.risk_score : "-";

    if (data.risk_level === "HIGH") riskEl.style.color = "red";
    else if (data.risk_level === "MEDIUM") riskEl.style.color = "orange";
    else riskEl.style.color = "lightgreen";

    // Detailed entity lists
    entitiesEl.innerHTML = `
        <p><b>Emails:</b> ${(data.email || []).join(", ") || "None"}</p>
        <p><b>Phones:</b> ${(data.phone || []).join(", ") || "None"}</p>
        <p><b>Credit Cards:</b> ${(data.credit_card || []).join(", ") || "None"}</p>
        <p><b>SSN:</b> ${(data.ssn || []).join(", ") || "None"}</p>
        <p><b>Aadhaar:</b> ${(data.aadhaar || []).join(", ") || "None"}</p>
        <p><b>IP Addresses:</b> ${(data.ip_address || []).join(", ") || "None"}</p>
        <p><b>Passwords:</b> ${(data.password || []).join(", ") || "None"}</p>
        <p><b>API Keys:</b> ${(data.api_key || []).join(", ") || "None"}</p>
        <p><b>Addresses:</b> ${(data.address || []).join(", ") || "None"}</p>
        <p><b>Names:</b> ${(data.names || []).join(", ") || "None"}</p>
        <p><b>Organizations:</b> ${(data.organizations || []).join(", ") || "None"}</p>
        <p><b>Locations:</b> ${(data.locations || []).join(", ") || "None"}</p>
    `;

    // Risk score breakdown (per-category contribution)
    if (data.risk_breakdown && Object.keys(data.risk_breakdown).length > 0) {
        const rows = Object.entries(data.risk_breakdown)
            .map(([cat, val]) => `<li>${cat}: +${val}</li>`)
            .join("");
        riskBreakdownEl.innerHTML = `<p><b>Risk Breakdown:</b></p><ul>${rows}</ul>`;
    } else {
        riskBreakdownEl.innerHTML = "";
    }

    // Anomaly / insider-threat behavioral check
    if (data.anomaly) {
        const flagged = data.anomaly.is_anomaly;
        anomalyPanelEl.innerHTML = `
            <p><b>${flagged ? "🚨 Anomaly Detected" : "✅ Normal Behavior"}:</b>
            ${data.anomaly.reason}</p>
        `;
        anomalyPanelEl.style.borderLeft = flagged ? "4px solid #ff4d4d" : "4px solid #4caf50";
    } else {
        anomalyPanelEl.innerHTML = "";
    }

    highlightedTextEl.innerHTML = data.highlighted_text || "";
}
