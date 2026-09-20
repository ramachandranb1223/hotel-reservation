/**
 * Grand Luxe Hotel - Core Frontend Application Script
 * Modular Vanilla JavaScript ES6+
 */

// Global Toast Notification Manager
function showToast(message, type = 'success') {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    const icon = type === 'success' ? '✓' : (type === 'error' ? '✕' : 'ℹ');
    
    toast.innerHTML = `
        <span style="font-weight:bold; font-size:1.1rem;">${icon}</span>
        <div style="flex-grow:1; font-size:0.92rem;">${message}</div>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(10px)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// Modal Helpers
function openModal(modalId) {
    const el = document.getElementById(modalId);
    if (el) {
        el.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(modalId) {
    const el = document.getElementById(modalId);
    if (el) {
        el.classList.remove('active');
        document.body.style.overflow = '';
    }
}

// Global API Request Helper
async function apiRequest(endpoint, options = {}) {
    const defaults = {
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    };
    const config = { ...defaults, ...options };
    if (options.body && typeof options.body === 'object') {
        config.body = JSON.stringify(options.body);
    }

    try {
        const response = await fetch(endpoint, config);
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || `HTTP error ${response.status}`);
        }
        return data;
    } catch (err) {
        console.error(`API Error on [${endpoint}]:`, err);
        throw err;
    }
}

// Close modals on clicking overlay backdrop
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.modal-overlay').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.remove('active');
                document.body.style.overflow = '';
            }
        });
    });
});
