// web_ui/static/js/modules/status.js
import { botStatusSpan, statusIndicator, startButton, stopButton, restartButton, featureListDiv } from './elements.js';
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

        // Remove features that no longer exist in the data
        Array.from(featureListDiv.children).forEach(colDiv => {
            const checkbox = colDiv.querySelector('input[type="checkbox"]');
            if (checkbox && !existingFeatures.has(checkbox.id)) {
                colDiv.remove();
            }
        });
        // Remove the "Bot is stopped" message if it exists
        const stoppedMessage = featureListDiv.querySelector('.text-muted');
        if (stoppedMessage) {
            stoppedMessage.remove();
        }

    } else {
        botStatusSpan.textContent = 'Stopped';
        statusIndicator.className = 'status-indicator stopped';
        startButton.disabled = false;
        stopButton.disabled = true;
        restartButton.style.display = 'none'; // Hide restart button

        // Display message only if no features are present
        if (featureListDiv.children.length === 0) {
            featureListDiv.innerHTML = '<p class="text-muted">Bot is stopped and features are not displayed.</p>';
        }
    }
}
