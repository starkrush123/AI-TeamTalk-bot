// web_ui/static/js/modules/config.js
import { showFlashMessage } from './utils.js';
import { configAccordion } from './elements.js';

export let currentConfig = {};

export async function fetchConfig() {
    try {
        const response = await fetch('/config');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const config = await response.json();
        currentConfig = config; // Update global config
        renderConfigForm(currentConfig);
    } catch (error) {
        console.error("Error fetching config:", error);
        showFlashMessage(`Error loading configuration: ${error.message}`, 'danger');
    }
}

export function renderConfigForm(config) {
    configAccordion.innerHTML = '';
    let accordionIdCounter = 0;

    for (const section in config) {
        if (section === 'WebUI') {
            continue; // Skip rendering the WebUI section
        }
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

export function getConfigFromForm() {
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
