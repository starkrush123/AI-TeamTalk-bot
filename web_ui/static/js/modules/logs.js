// web_ui/static/js/modules/logs.js
import { logContainer } from './elements.js';

let logLines = [];
const MAX_LOG_LINES = 500; // Batasi jumlah baris log yang ditampilkan

export async function fetchLogs() {
    const response = await fetch('/logs?limit=500'); // Ambil 500 baris terakhir dari server
    const newLogsText = await response.text();
    const newLines = newLogsText.split(/\r?\n/).filter(line => line.trim() !== '');

    // Find new lines to append
    let linesToAppend = [];
    if (logLines.length === 0) {
        linesToAppend = newLines;
    } else {
        const lastKnownLog = logLines[logLines.length - 1];
        let found = false;
        for (let i = 0; i < newLines.length; i++) {
            if (newLines[i].includes(lastKnownLog)) {
                found = true;
                linesToAppend = newLines.slice(i + 1);
                break;
            }
        }
        if (!found) { // If last known log not found, assume full refresh
            linesToAppend = newLines;
            logContainer.innerHTML = ''; // Clear existing logs
            logLines = [];
        }
    }

    // Append new lines to the DOM and internal array
    const fragment = document.createDocumentFragment();
    linesToAppend.forEach(line => {
        const logEntry = document.createElement('div');
        logEntry.textContent = line;
        fragment.appendChild(logEntry);
        logLines.push(line);
    });
    logContainer.appendChild(fragment);

    // Trim old lines from DOM and internal array if over limit
    while (logLines.length > MAX_LOG_LINES) {
        logContainer.removeChild(logContainer.firstChild);
        logLines.shift();
    }

    logContainer.scrollTop = logContainer.scrollHeight; // Scroll ke bawah
}