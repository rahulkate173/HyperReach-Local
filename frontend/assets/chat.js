async function sendMessage() {
    const input = document.getElementById("userInput");
    const message = input.value.trim();
    if (!message) return;

    addUserMessage(message);
    input.value = "";

    try {
        const response = await fetch("http://127.0.0.1:5000/api/analyze", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                platform: "linkedin",
                profile_data: {
                    name: message,
                    role: "Software Engineer",
                    company: "TechCorp",
                    bio: "Passionate about building scalable systems.",
                    recent_activity: ["Working on AI projects", "Love clean code"]
                }
            })
        });

        const data = await response.json();

        if (!response.ok) {
            addAIMessage("⚠️ " + data.error);
            return;
        }

        addAIMessage(`
            <strong>${data.profile.name}</strong><br>
            Role: ${data.profile.role}<br>
            Company: ${data.profile.company}<br>
            Style: ${data.profile.communication_style}<br>
            Seniority: ${data.profile.seniority}<br><br>
            Pain Points: ${data.insights.pain_points.join(", ")}<br>
            Best Channels: ${data.insights.best_channels.join(", ")}<br><br>
            Remaining Requests: ${data.remaining_requests}
        `);

    } catch (error) {
        addAIMessage("⚠️ Server connection failed.");
        console.error(error);
    }
}
