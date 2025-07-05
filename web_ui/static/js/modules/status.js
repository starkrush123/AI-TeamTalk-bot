// web_ui/static/js/modules/status.js
import { botStatusSpan, statusIndicator, startButton, stopButton, restartButton, featureListDiv, serverInfoCard, serverInfoDisplay } from './elements.js';
import { showFlashMessage } from './utils.js';

const featureMap = {
    "announce_join_leave": "jcl",
    "allow_channel_messages": "chanmsg",
    "allow_broadcast": "broadcast",
    "allow_gemini_pm": "geminipm",
    "allow_gemini_channel": "geminichan",
    "filter_enabled": "filter",
    "bot_locked": "lock",
    "context_history_enabled": "context_history",
    "debug_logging_enabled": "debug_logging"
};

export async function fetchStatus() {
    const response = await fetch('/status');
    const data = await response.json();
    
    if (data.running) {
        botStatusSpan.textContent = 'Running';
        statusIndicator.className = 'status-indicator running';
        startButton.disabled = true;
        stopButton.disabled = false;
        restartButton.style.display = 'inline-block'; // Show restart button

        // Clear any previous messages or features when bot is running
        featureListDiv.innerHTML = '';

        // Update features when bot is running
        const existingFeatures = new Set();
        if (data.features) {
            for (const fullKey in data.features) {
                const shortKey = featureMap[fullKey] || fullKey; // Use short key if available
                const isEnabled = data.features[fullKey];
                const inputId = `feature-${shortKey}`;
                existingFeatures.add(inputId);

                let checkbox = document.getElementById(inputId);
                if (!checkbox) {
                    // Feature does not exist, create it
                    const colDiv = document.createElement('div');
                    colDiv.className = 'col';
                    colDiv.innerHTML = `
                        <div class="form-check form-switch feature-card">
                            <input class="form-check-input" type="checkbox" role="switch" id="${inputId}">
                            <label class="form-check-label" for="${inputId}">${fullKey.replace(/_/g, ' ').toUpperCase()}</label>
                        </div>
                    `;
                    featureListDiv.appendChild(colDiv);
                    checkbox = document.getElementById(inputId);
                    if (checkbox) {
                        checkbox.addEventListener('change', async (event) => {
                            const toggleResponse = await fetch(`/toggle_feature/${shortKey}`, {
                                method: 'POST',
                            });
                            const toggleData = await toggleResponse.json();
                            if (toggleData.status === 'success') {
                                console.log(toggleData.message);
                                fetchStatus(); // Refresh status to show updated state
                            } else {
                                alert(`Error toggling feature: ${toggleData.message}`);
                                event.target.checked = !event.target.checked; // Revert checkbox state
                            }
                        });
                    }
                }

                // Update existing checkbox properties
                if (checkbox) {
                    checkbox.checked = isEnabled;
                    checkbox.disabled = !data.running;
                }
            }
        }

        // Show server info card
        serverInfoCard.style.display = 'block';

        // Populate server info
        if (data.server_info) {
            serverInfoDisplay.innerHTML = ''; // Clear previous content
            const infoMap = {
                "host": "Host",
                "tcp_port": "TCP Port",
                "udp_port": "UDP Port",
                "nickname": "Nickname",
                "username": "Username",
                "target_channel_path": "Target Channel",
                "my_user_id": "My User ID",
                "my_rights": "My Rights",
                "client_name": "Client Name",
                "status_message": "Status Message",
                "logged_in": "Logged In",
                "in_channel": "In Channel"
            };

            for (const key in infoMap) {
                if (data.server_info.hasOwnProperty(key)) {
                    const value = data.server_info[key];
                    const displayValue = typeof value === 'boolean' ? (value ? 'Yes' : 'No') : value;
                    const colDiv = document.createElement('div');
                    colDiv.className = 'col-md-6 col-12';
                    colDiv.innerHTML = `<p><strong>${infoMap[key]}:</strong> ${displayValue}</p>`;
                    serverInfoDisplay.appendChild(colDiv);
                }
            }
        }

    } else {
        updateUIForStoppedBot();
    }
}

export function updateUIForStoppedBot() {
    botStatusSpan.textContent = 'Stopped';
    statusIndicator.className = 'status-indicator stopped';
    startButton.disabled = false;
    stopButton.disabled = true;
    restartButton.style.display = 'none'; // Hide restart button

    // Hide server info card
    serverInfoCard.style.display = 'none';

    // Always display the stopped message and clear features
    featureListDiv.innerHTML = '<p class="text-muted">Bot is stopped and features are not displayed.</p>';
}
