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
const explanationPanelEl = document.getElementById("explanationPanel");
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

dropZone.ondragover = (e) => {
    e.preventDefault();
    dropZone.classList.add("drag-active");
};
dropZone.ondragleave = () => dropZone.classList.remove("drag-active");
dropZone.ondrop = (e) => {
    e.preventDefault();
    dropZone.classList.remove("drag-active");
    if (e.dataTransfer.files[0]) uploadFile(e.dataTransfer.files[0]);
};

fileInput.onchange = () => {
    if (fileInput.files[0]) uploadFile(fileInput.files[0]);
};

// Renders a category's matches as "value (NN%)" chips, or "None".
// Accepts either the new {value, confidence} objects or plain strings,
// so this keeps working even against an older API response shape.
function formatMatches(list) {
    if (!list || list.length === 0) return "None";
    return list
        .map(m => {
            if (typeof m === "string") return m;
            const pct = Math.round((m.confidence ?? 1) * 100);
            const level = pct >= 80 ? "conf-high" : pct >= 55 ? "conf-med" : "conf-low";
            return `${m.value} <span class="confidence-badge ${level}">${pct}%</span>`;
        })
        .join(", ");
}

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
    riskScoreEl.innerText = data.risk_score !== undefined ? data.risk_score + "%" : "-";
    if (data.risk_level === "HIGH") riskEl.style.color = "red";
    else if (data.risk_level === "MEDIUM") riskEl.style.color = "orange";
    else riskEl.style.color = "lightgreen";

    // Detailed entity lists - each match shown with its confidence %
    entitiesEl.innerHTML = `
        <p><b>Emails:</b> ${formatMatches(data.email)}</p>
        <p><b>Phones:</b> ${formatMatches(data.phone)}</p>
        <p><b>Credit Cards:</b> ${formatMatches(data.credit_card)}</p>
        <p><b>SSN:</b> ${formatMatches(data.ssn)}</p>
        <p><b>Aadhaar:</b> ${formatMatches(data.aadhaar)}</p>
        <p><b>IP Addresses:</b> ${formatMatches(data.ip_address)}</p>
        <p><b>Passwords:</b> ${formatMatches(data.password)}</p>
        <p><b>API Keys:</b> ${formatMatches(data.api_key)}</p>
        <p><b>Addresses:</b> ${formatMatches(data.address)}</p>
        <p><b>Names:</b> ${formatMatches(data.names)}</p>
        <p><b>Organizations:</b> ${formatMatches(data.organizations)}</p>
        <p><b>Locations:</b> ${formatMatches(data.locations)}</p>
    `;

    // Risk score breakdown (per-category contribution, now confidence-weighted)
    if (data.risk_breakdown && Object.keys(data.risk_breakdown).length > 0) {
        const rows = Object.entries(data.risk_breakdown)
            .map(([cat, val]) => {
                const conf = data.confidence_breakdown ? data.confidence_breakdown[cat] : undefined;
                const confText = conf !== undefined ? ` <span style="opacity:0.7">(avg confidence: ${Math.round(conf * 100)}%)</span>` : "";
                return `<li>${cat}: +${val}${confText}</li>`;
            })
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

    // Explainable AI - why BERT flagged this as sensitive
    if (data.explanation && data.explanation.available) {
        const wordRows = data.explanation.top_words
            .map(tw => {
                const color = tw.weight > 0 ? "#ff8a80" : "#80cbc4";
                const sign = tw.weight > 0 ? "+" : "";
                return `<li><b>${tw.word}</b>: <span style="color:${color}">${sign}${tw.weight}</span></li>`;
            })
            .join("");
        explanationPanelEl.innerHTML = `
            <p><b>🧠 Why BERT flagged this:</b></p>
            <p>${data.explanation.summary}</p>
            <ul>${wordRows}</ul>
            <p style="font-size:0.8em; opacity:0.7;">Red = pushed toward "sensitive", Teal = pushed away from it</p>
        `;
    } else if (data.explanation) {
        explanationPanelEl.innerHTML = `<p style="opacity:0.6;">${data.explanation.summary}</p>`;
    } else {
        explanationPanelEl.innerHTML = "";
    }

    highlightedTextEl.innerHTML = data.highlighted_text || "";
}
