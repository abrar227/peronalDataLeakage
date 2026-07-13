function scanText() {
    let text = document.getElementById("inputText").value;

    fetch("/scan", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ text: text })
    })
    .then(res => res.json())
    .then(data => {
        document.getElementById("resultBox").classList.remove("hidden");

        document.getElementById("risk").innerText = data.risk_level;

        document.getElementById("entities").innerHTML = `
            <p><b>Emails:</b> ${data.email.join(", ")}</p>
            <p><b>Phones:</b> ${data.phone.join(", ")}</p>
            <p><b>Names:</b> ${data.names.join(", ")}</p>
            <p><b>Organizations:</b> ${data.organizations.join(", ")}</p>
            <p><b>Locations:</b> ${data.locations.join(", ")}</p>
        `;

        document.getElementById("highlightedText").innerHTML =
            data.highlighted_text;
    });
}