// web_ui/static/js/modules/eventHandlers.js
import { startButton, stopButton, restartButton, saveConfigButton, addUserModalElement } from './elements.js';
import { showFlashMessage } from './utils.js';
import { fetchStatus } from './status.js';
import { getConfigFromForm, fetchConfig } from './config.js';
import { fetchUsers, setupAddUserForm } from './users.js';
import { fetchLogs } from './logs.js';

export function setupEventListeners() {
    addUserModalElement.addEventListener('shown.bs.modal', () => {
        newUsernameInput.focus();
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
            fetchConfig();
        } else if (activeTabId === 'user-management-tab') {
            fetchUsers();
        } else if (activeTabId === 'logs-tab') {
            fetchLogs();
        }
    });

    setupAddUserForm();
}
