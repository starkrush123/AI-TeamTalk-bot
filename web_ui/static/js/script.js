const botStatusSpan = document.getElementById('botStatus');
const statusIndicator = document.getElementById('statusIndicator');
const startButton = document.getElementById('startButton');
const stopButton = document.getElementById('stopButton');
const restartButton = document.getElementById('restartButton');
const refreshButton = document.getElementById('refreshButton');
const featureListDiv = document.getElementById('featureList');
const configAccordion = document.getElementById('configAccordion');
const saveConfigButton = document.getElementById('saveConfigButton');
const logContainer = document.getElementById('logContainer');
const userListTableBody = document.getElementById('userListTableBody');
const addUserForm = document.getElementById('addUserForm');
const newUsernameInput = document.getElementById('newUsername');
const newPasswordInput = document.getElementById('newPassword');
const confirmPasswordInput = document.getElementById('confirmPassword');
const addUserModalElement = document.getElementById('addUserModal');
const addUserModal = new bootstrap.Modal(addUserModalElement);

// Autofocus for Add User Modal
addUserModalElement.addEventListener('shown.bs.modal', () => {
    newUsernameInput.focus();
});

let currentConfig = {}; // To store the fetched config for editing

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

// Function to display flash messages
function showFlashMessage(message, category) {
    const alertContainer = document.createElement('div');
    alertContainer.className = `alert alert-${category} alert-dismissible fade show mt-3`;
    alertContainer.setAttribute('role', 'alert');
    alertContainer.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    document.querySelector('.container').prepend(alertContainer);
    setTimeout(() => alertContainer.remove(), 5000); // Remove after 5 seconds
}

async function fetchStatus() {
    const response = await fetch('/status');
    const data = await response.json();
    
    if (data.running) {
        botStatusSpan.textContent = 'Running';
        statusIndicator.className = 'status-indicator running';
        startButton.disabled = true;
        stopButton.disabled = false;
        restartButton.style.display = 'inline-block'; // Show restart button
    } else {
        botStatusSpan.textContent = 'Stopped';
        statusIndicator.className = 'status-indicator stopped';
        startButton.disabled = false;
        stopButton.disabled = true;
        restartButton.style.display = 'none'; // Hide restart button
    }

    // Update features
    featureListDiv.innerHTML = '';
    if (data.features) {
        for (const fullKey in data.features) {
            const shortKey = featureMap[fullKey] || fullKey; // Use short key if available
            const isEnabled = data.features[fullKey];
            const colDiv = document.createElement('div');
            colDiv.className = 'col';
            colDiv.innerHTML = `
                <div class="form-check form-switch feature-card">
                    <input class="form-check-input" type="checkbox" role="switch" id="feature-${shortKey}" ${isEnabled ? 'checked' : ''} ${!data.running ? 'disabled' : ''}>
                    <label class="form-check-label" for="feature-${shortKey}">${fullKey.replace(/_/g, ' ').toUpperCase()}</label>
                </div>
            `;
            featureListDiv.appendChild(colDiv);

            const checkbox = colDiv.querySelector(`#feature-${shortKey}`);
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
    }

    // Update config editor
    if (data.config) {
        currentConfig = data.config;
        renderConfigForm(currentConfig);
    } else {
        // If bot not running, try to fetch config directly
        const configResponse = await fetch('/config');
        if (configResponse.ok) {
            currentConfig = await configResponse.json();
            renderConfigForm(currentConfig);
        } else {
            configAccordion.innerHTML = '<p class="text-danger">Failed to load configuration.</p>';
        }
    }
}

function renderConfigForm(config) {
    configAccordion.innerHTML = '';
    let accordionIdCounter = 0;

    for (const section in config) {
        const sectionId = `collapse-${accordionIdCounter++}`;
        const sectionHeaderId = `heading-${sectionId}`;
        const isConnectionSection = section === 'Connection';

        const accordionItem = document.createElement('div');
        accordionItem.className = 'accordion-item';
        accordionItem.innerHTML = `
            <h2 class="accordion-header" id="${sectionHeaderId}">
                <button class="accordion-button ${isConnectionSection ? '' : 'collapsed'}" type="button" data-bs-toggle="collapse" data-bs-target="#${sectionId}" aria-expanded="${isConnectionSection ? 'true' : 'false'}" aria-controls="${sectionId}">
                    ${section.replace(/_/g, ' ').toUpperCase()}
                </button>
            </h2>
            <div id="${sectionId}" class="accordion-collapse collapse ${isConnectionSection ? 'show' : ''}" aria-labelledby="${sectionHeaderId}" data-bs-parent="#configAccordion">
                <div class="accordion-body">
                    <form id="form-${section}"></form>
                </div>
            </div>
        `;
        configAccordion.appendChild(accordionItem);

        const form = accordionItem.querySelector(`#form-${section}`);
        for (const key in config[section]) {
            const value = config[section][key];
            const inputId = `${section}-${key}`;
            let inputHtml = '';
            let inputType = 'text';

            if (key.includes('password') || key.includes('api_key')) {
                inputType = 'password';
            } else if (typeof value === 'boolean' || value === 'True' || value === 'False') {
                inputType = 'checkbox';
            } else if (!isNaN(value) && !isNaN(parseFloat(value))) { // Check if it's a number
                inputType = 'number';
            }

            if (inputType === 'checkbox') {
                inputHtml = `
                    <div class="form-check form-switch mb-3">
                        <input class="form-check-input" type="checkbox" role="switch" id="${inputId}" ${value === true || value === 'True' ? 'checked' : ''}>
                        <label class="form-check-label" for="${inputId}">${key.replace(/_/g, ' ').toUpperCase()}</label>
                    </div>
                `;
            } else if (key === 'ai_system_instructions' || key === 'welcome_message_instructions') {
                 inputHtml = `
                    <div class="mb-3">
                        <label for="${inputId}" class="form-label">${key.replace(/_/g, ' ').toUpperCase()}</label>
                        <textarea class="form-control" id="${inputId}" rows="3">${value}</textarea>
                    </div>
                `;
            } else {
                inputHtml = `
                    <div class="mb-3">
                        <label for="${inputId}" class="form-label">${key.replace(/_/g, ' ').toUpperCase()}</label>
                        <input type="${inputType}" class="form-control" id="${inputId}" value="${value}">
                    </div>
                `;
            }
            form.insertAdjacentHTML('beforeend', inputHtml);
        }
    }
}

function getConfigFromForm() {
    const newConfig = JSON.parse(JSON.stringify(currentConfig)); // Deep copy
    for (const section in newConfig) {
        for (const key in newConfig[section]) {
            const inputId = `${section}-${key}`;
            const inputElement = document.getElementById(inputId);
            if (inputElement) {
                if (inputElement.type === 'checkbox') {
                    newConfig[section][key] = inputElement.checked ? 'True' : 'False'; // Store as string 'True'/'False'
                } else if (inputElement.type === 'number') {
                    newConfig[section][key] = inputElement.value; // Store as string, Flask will convert
                } else {
                    newConfig[section][key] = inputElement.value;
                }
            }
        }
    }
    return newConfig;
}

let logLines = [];
const MAX_LOG_LINES = 500; // Batasi jumlah baris log yang ditampilkan

async function fetchLogs() {
    const response = await fetch('/logs?limit=500'); // Ambil 500 baris terakhir dari server
    const newLogsText = await response.text();
    const newLines = newLogsText.split(/\r?\n/);

    // Filter out empty lines that might result from split
    const filteredNewLines = newLines.filter(line => line.trim() !== '');

    // Tambahkan hanya baris baru yang belum ada
    const lastKnownLog = logLines.length > 0 ? logLines[logLines.length - 1] : '';
    let startIndex = 0;
    if (lastKnownLog) {
        for (let i = 0; i < filteredNewLines.length; i++) {
            if (filteredNewLines[i].includes(lastKnownLog)) { // Cek apakah baris terakhir sudah ada
                startIndex = i + 1;
                break;
            }
        }
    }
    
    const logsToAppend = filteredNewLines.slice(startIndex);
    logLines = logLines.concat(logsToAppend);

    // Batasi jumlah baris log
    if (logLines.length > MAX_LOG_LINES) {
        logLines = logLines.slice(logLines.length - MAX_LOG_LINES);
    }

    logContainer.textContent = logLines.join('\n');
    logContainer.scrollTop = logContainer.scrollHeight; // Scroll ke bawah
}

async function fetchUsers() {
    const response = await fetch('/users');
    const users = await response.json();
    userListTableBody.innerHTML = '';
    users.forEach(user => {
        const row = userListTableBody.insertRow();
        row.innerHTML = `
            <td>${user.username}</td>
            <td>
                <button class="btn btn-danger btn-sm delete-user-btn" data-user-id="${user.id}">Delete</button>
            </td>
        `;
    });
    // Add event listeners for delete buttons
    document.querySelectorAll('.delete-user-btn').forEach(button => {
        button.addEventListener('click', async (event) => {
            const userId = event.target.dataset.userId;
            if (confirm(`Are you sure you want to delete user ${userId}?`)) {
                const response = await fetch(`/users/${userId}`, {
                    method: 'DELETE',
                });
                const data = await response.json();
                if (data.status === 'success') {
                    showFlashMessage(data.message, 'success');
                    fetchUsers(); // Refresh user list
                } else {
                    showFlashMessage(data.message, 'danger');
                }
            }
        });
    });
}

// Event listener for adding a new user
addUserForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    const username = newUsernameInput.value;
    const password = newPasswordInput.value;
    const confirmPassword = confirmPasswordInput.value;

    if (password !== confirmPassword) {
        showFlashMessage('Passwords do not match.', 'danger');
        return;
    }

    const response = await fetch('/users', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
    });
    const data = await response.json();
    if (data.status === 'success') {
        showFlashMessage(data.message, 'success');
        addUserModal.hide(); // Close the modal
        addUserForm.reset(); // Clear the form
        fetchUsers(); // Refresh user list
    } else {
        showFlashMessage(data.message, 'danger');
    }
});

startButton.addEventListener('click', async () => {
    const response = await fetch('/start', { method: 'POST' });
    const data = await response.json();
    showFlashMessage(data.message, data.status === 'success' ? 'success' : 'danger');
    fetchStatus();
});

stopButton.addEventListener('click', async () => {
    const response = await fetch('/stop', { method: 'POST' });
    const data = await response.json();
    showFlashMessage(data.message, data.status === 'success' ? 'success' : 'danger');
    fetchStatus();
});

restartButton.addEventListener('click', async () => {
    const response = await fetch('/restart', { method: 'POST' });
    const data = await response.json();
    showFlashMessage(data.message, data.status === 'success' ? 'success' : 'danger');
    fetchStatus();
});

refreshButton.addEventListener('click', () => {
    fetchStatus();
    fetchLogs();
});

saveConfigButton.addEventListener('click', async () => {
    try {
        const newConfig = getConfigFromForm();
        const response = await fetch('/config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(newConfig)
        });
        const data = await response.json();
        showFlashMessage(data.message, data.status === 'success' ? 'success' : 'danger');
        if (data.status === 'success') {
            fetchStatus(); // Refresh status to show updated config
        }
    } catch (e) {
        showFlashMessage(`Error saving configuration: ${e.message}`, 'danger');
        console.error(e);
    }
});

// Tab handling
const myTabEl = document.querySelector('#myTab');
myTabEl.addEventListener('shown.bs.tab', event => {
    const activeTabId = event.target.id; // ID of the activated tab
    if (activeTabId === 'status-tab') {
        fetchStatus();
    } else if (activeTabId === 'settings-tab') {
        // Config is already fetched by fetchStatus, but ensure it's rendered
        if (Object.keys(currentConfig).length === 0) {
            fetchStatus(); // Re-fetch if somehow empty
        }
    } else if (activeTabId === 'user-management-tab') {
        fetchUsers();
    } else if (activeTabId === 'logs-tab') {
        fetchLogs();
    }
});

// Initial fetch for the active tab (Status tab is active by default)
fetchStatus();
fetchLogs(); // Always fetch logs initially, as it's a common need

// Refresh logs every 5 seconds, regardless of tab, but only if logs tab is active
setInterval(() => {
    const logsTab = document.getElementById('logs-tab');
    if (logsTab && logsTab.classList.contains('active')) {
        fetchLogs();
    }
}, 5000);