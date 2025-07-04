// web_ui/static/js/modules/utils.js
export function showFlashMessage(message, category) {
    const alertContainer = document.createElement('div');
    alertContainer.className = `alert alert-${category} alert-dismissible fade show mt-3`;
    alertContainer.setAttribute('role', 'alert');
    alertContainer.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    document.querySelector('.container').prepend(alertContainer);
    setTimeout(() => alertContainer.remove(), 5000);
}
