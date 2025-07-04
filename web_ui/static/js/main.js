// web_ui/static/js/main.js
import { fetchStatus } from './modules/status.js';
import { fetchLogs } from './modules/logs.js';
import { setupEventListeners } from './modules/eventHandlers.js';

// Initial setup
setupEventListeners();
fetchStatus();

// Refresh status every 5 seconds
setInterval(fetchStatus, 5000);

// Refresh logs every 15 seconds, but only if logs tab is active
setInterval(() => {
    const logsTab = document.getElementById('logs-tab');
    if (logsTab && logsTab.classList.contains('active')) {
        fetchLogs();
    }
}, 15000);
