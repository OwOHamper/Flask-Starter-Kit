let activeToasts = [];
const TOAST_MARGIN = 10; // Margin between toasts in pixels

function showToast(type, message, duration = 3000) {
    const toastId = `toast-${type}`;
    const originalToast = document.getElementById(toastId);
    
    if (!originalToast) {
        console.error(`Toast with id ${toastId} not found`);
        return;
    }

    // Clone the original toast
    const toast = originalToast.cloneNode(true);
    toast.id = `${toastId}-${Date.now()}`;

    // Update the message
    const messageElement = toast.querySelector('.ms-3.text-sm.font-normal');
    if (messageElement) {
        messageElement.textContent = message;
    }

    // Set up the toast
    toast.style.position = 'fixed';
    toast.style.right = '-100%';
    toast.style.zIndex = '9999';
    toast.style.transition = 'right 0.5s ease-in-out, top 0.5s ease-in-out';
    toast.classList.remove('hidden');
    toast.classList.add('flex');

    // Add the toast to the document
    document.body.appendChild(toast);

    // Position the toast
    positionToast(toast);

    // Animate in
    setTimeout(() => {
        toast.style.right = '1rem';
    }, 100);

    // Set up auto-dismiss
    const timeoutId = setTimeout(() => {
        hideToast(toast);
    }, duration);

    // Set up manual dismiss
    const dismissButton = toast.querySelector('[data-dismiss-target]');
    if (dismissButton) {
        dismissButton.addEventListener('click', () => hideToast(toast));
    }

    // Add to active toasts
    activeToasts.push({ element: toast, timeoutId });
}

function positionToast(toast) {
    const toastHeight = toast.offsetHeight;
    let topPosition = 16; // Initial top margin

    for (const activeToast of activeToasts) {
        topPosition += activeToast.element.offsetHeight + TOAST_MARGIN;
    }

    toast.style.top = `${topPosition}px`;
}

function hideToast(toast) {
    toast.style.right = '-100%';
    
    toast.addEventListener('transitionend', function handler() {
        const index = activeToasts.findIndex(t => t.element === toast);
        if (index > -1) {
            clearTimeout(activeToasts[index].timeoutId);
            activeToasts.splice(index, 1);
        }
        toast.remove();
        toast.removeEventListener('transitionend', handler);
        
        // Reposition remaining toasts
        activeToasts.forEach((activeToast, i) => {
            const top = 16 + i * (activeToast.element.offsetHeight + TOAST_MARGIN);
            activeToast.element.style.top = `${top}px`;
        });
    });
}

document.addEventListener('DOMContentLoaded', function () {
    const toasts = document.querySelectorAll('[id^="toast-"]');
    toasts.forEach(toast => {
        // Ensure initial state
        toast.classList.add('hidden');
        toast.classList.remove('flex');
        toast.style.transition = 'right 0.5s ease-in-out, top 0.5s ease-in-out';
    });
});

// Usage examples:
// showToast('success', 'Item moved successfully.');
// showToast('danger', 'Item has been deleted.', 5000);
// showToast('warning', 'Improve password difficulty.', 4000);