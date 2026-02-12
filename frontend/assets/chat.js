// Chat interface functionality

const API_BASE_URL = 'http://127.0.0.1:8000/api';
const chatMessagesDiv = document.getElementById('chatMessages');
const userInput = document.getElementById('userInput');

// Store conversation state
let conversationState = {
    step: 'initial',
    profileUrl: null,
    platform: null,
    selectedChannels: ['email', 'linkedin_dm', 'whatsapp'],
    generatedMessages: null
};

async function sendMessage() {
    const message = userInput.value.trim();
    if (!message) return;

    // Add user message to chat
    addMessage(message, 'user');
    userInput.value = '';

    // Process based on conversation state
    await handleUserInput(message);
}

function handleKeyPress(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
}

async function handleUserInput(input) {
    try {
        // Show loading indicator
        showLoadingIndicator();

        if (conversationState.step === 'initial') {
            // First message - expecting profile URL or description
            await handleProfileInput(input);
        } else if (conversationState.step === 'confirm_profile') {
            // Confirm and proceed
            await handleGenerateMessages();
        }
    } catch (error) {
        addMessage(`❌ Error: ${error.message}`, 'ai');
        console.error(error);
    }
}

async function handleProfileInput(input) {
    try {
        conversationState.profileUrl = input;
        conversationState.platform = 'linkedin'; // Default platform

        // Show that we're analyzing
        addMessage('🔍 Analyzing profile...', 'ai');

        // Call API to analyze profile
        const response = await fetch(`${API_BASE_URL}/analyze-profile`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                profile_url: input,
                platform: conversationState.platform
            })
        });

        if (!response.ok) {
            throw new Error(`API error: ${response.statusText}`);
        }

        const profile = await response.json();

        // Display profile information
        const profileInfo = `
            ✓ <strong>Profile Analyzed!</strong><br>
            <br>
            <strong>Name:</strong> ${profile.name}<br>
            <strong>Role:</strong> ${profile.role}<br>
            <strong>Company:</strong> ${profile.company}<br>
            <strong>Industry:</strong> ${profile.industry}<br>
            <strong>Seniority:</strong> ${profile.seniority_level}<br>
            <strong>Communication Style:</strong> ${profile.communication_style}<br>
            <strong>Skills:</strong> ${profile.skills.slice(0, 3).join(', ')}<br>
            <br>
            Ready to generate personalized messages? Type <strong>"generate"</strong> to proceed.
        `;

        addMessage(profileInfo, 'ai');
        conversationState.step = 'confirm_profile';
        conversationState.profile = profile;

    } catch (error) {
        addMessage(`Error analyzing profile: ${error.message}`, 'ai');
        console.error(error);
    }
}

async function handleGenerateMessages() {
    try {
        addMessage('⚡ Generating personalized messages...', 'ai');

        const response = await fetch(`${API_BASE_URL}/generate-outreach`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                profile_url: conversationState.profileUrl,
                platform: conversationState.platform,
                channels: conversationState.selectedChannels,
                additional_context: null
            })
        });

        if (!response.ok) {
            throw new Error(`API error: ${response.statusText}`);
        }

        const result = await response.json();
        conversationState.generatedMessages = result;

        // Display generated messages
        let messageContent = '✅ <strong>Messages Generated Successfully!</strong><br><br>';

        if (result.messages && result.messages.length > 0) {
            messageContent += `Generated <strong>${result.messages.length} messages</strong> for ${result.profile.name}:<br><br>`;

            result.messages.forEach((msg, idx) => {
                const replyRate = msg.estimated_reply_rate 
                    ? Math.round(msg.estimated_reply_rate * 100)
                    : 'N/A';
                    
                messageContent += `<strong>${idx + 1}. ${msg.channel.toUpperCase()}</strong> `;
                messageContent += `<em>(Reply Rate: ${replyRate}%)</em><br>`;
                messageContent += `<a href="#" onclick="showMessageDetail(${idx}); return false;" style="color: #6366f1; text-decoration: underline;">View Message</a><br><br>`;
            });
        }

        messageContent += '<br><strong>What would you like to do?</strong><br>';
        messageContent += 'Type <strong>"new"</strong> to analyze another profile or <strong>"export"</strong> to download messages.';

        addMessage(messageContent, 'ai');
        conversationState.step = 'messages_generated';

    } catch (error) {
        addMessage(`Error generating messages: ${error.message}`, 'ai');
        console.error(error);
    }
}

function showMessageDetail(messageIndex) {
    const msg = conversationState.generatedMessages.messages[messageIndex];
    const modal = document.getElementById('messageModal');
    const title = document.getElementById('modalTitle');
    const content = document.getElementById('modalContent');

    title.textContent = `${msg.channel.toUpperCase()} Message`;

    let detailHTML = `
        <div style="background-color: #f9fafb; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem;">
            <p><strong>Tone:</strong> ${msg.tone}</p>
            <p><strong>Estimated Reply Rate:</strong> ${Math.round(msg.estimated_reply_rate * 100)}%</p>
    `;

    if (msg.subject) {
        detailHTML += `<p><strong>Subject:</strong> ${msg.subject}</p>`;
    }

    detailHTML += `</div>`;

    detailHTML += `
        <div style="background-color: white; border: 1px solid #e5e7eb; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem; font-family: 'Monaco', monospace; line-height: 1.6;">
            <p>${msg.content.split('\n').join('<br>')}</p>
        </div>
    `;

    detailHTML += `
        <div style="background-color: #f0f9ff; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #6366f1;">
            <strong>Call to Action:</strong> ${msg.cta}
        </div>
    `;

    content.innerHTML = detailHTML;
    modal.style.display = 'flex';
    modal.style.alignItems = 'center';
    modal.style.justifyContent = 'center';
}

function closeModal() {
    document.getElementById('messageModal').style.display = 'none';
}

function addMessage(message, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;

    const avatarDiv = document.createElement('div');
    avatarDiv.className = `message-avatar ${sender}`;
    avatarDiv.textContent = sender === 'user' ? '👤' : '🤖';

    const bubbleDiv = document.createElement('div');
    bubbleDiv.className = 'message-bubble';
    bubbleDiv.innerHTML = message;

    messageDiv.appendChild(avatarDiv);
    messageDiv.appendChild(bubbleDiv);

    chatMessagesDiv.appendChild(messageDiv);

    // Auto scroll to bottom
    chatMessagesDiv.scrollTop = chatMessagesDiv.scrollHeight;
}

function showLoadingIndicator() {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message ai';
    messageDiv.id = 'loadingIndicator';

    const avatarDiv = document.createElement('div');
    avatarDiv.className = 'message-avatar ai';
    avatarDiv.textContent = '🤖';

    const bubbleDiv = document.createElement('div');
    bubbleDiv.className = 'message-bubble loading';
    bubbleDiv.innerHTML = '<span></span><span></span><span></span>';

    messageDiv.appendChild(avatarDiv);
    messageDiv.appendChild(bubbleDiv);

    chatMessagesDiv.appendChild(messageDiv);
    chatMessagesDiv.scrollTop = chatMessagesDiv.scrollHeight;
}

function removeLoadingIndicator() {
    const loading = document.getElementById('loadingIndicator');
    if (loading) {
        loading.remove();
    }
}

// Override original handleUserInput to remove loading
const originalHandleUserInput = handleUserInput;
async function handleUserInputWithLoading(input) {
    try {
        await originalHandleUserInput(input);
    } finally {
        removeLoadingIndicator();
    }
}

// Monkey patch
window.handleUserInput = handleUserInputWithLoading;

// Initialize welcome message
document.addEventListener('DOMContentLoaded', () => {
    console.log('Chat interface loaded');
});

// Close modal when clicking outside
document.addEventListener('click', (e) => {
    const modal = document.getElementById('messageModal');
    if (e.target === modal) {
        closeModal();
    }
});

// Focus input on load
window.addEventListener('load', () => {
    userInput.focus();
});
