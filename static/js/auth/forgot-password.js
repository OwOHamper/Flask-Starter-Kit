document.addEventListener('DOMContentLoaded', function() {
    const resetPasswordButton = document.getElementById('resetPasswordButton');
    resetPasswordButton.addEventListener('click', validateAndSubmit);
});

function validateAndSubmit() {
    const resetPasswordButton = document.getElementById('resetPasswordButton');
    const loadingSpinner = document.getElementById('loading-spinner');

    const email = document.getElementById('email').value.trim();
    const terms = document.getElementById('terms').checked;
    const csrfToken = document.getElementById('csrf').value;

    if (email === '') {
        showToast('danger', 'Please enter your email address.', 3000);
        return;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        showToast('danger', 'Please enter a valid email address.', 3000);
        return;
    }

    if (!terms) {
        showToast('danger', 'Please accept the Terms and Conditions.', 3000);
        return;
    }

    resetPasswordButton.disabled = true;
    resetPasswordButton.classList.add('opacity-60', 'cursor-not-allowed');
    loadingSpinner.classList.remove('hidden');


    // Use fetch to send the data to the server
    fetch('/forgot-password', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            "email": email,
            "_csrf_token": csrfToken
        }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('success', 'A password reset email has been sent.', 5000);
            loadingSpinner.classList.add('hidden');
            // document.getElementById('email').value = '';
            // document.getElementById('terms').checked = false;
        } else {
            showToast('danger', data.message || 'An error occurred. Please try again.', 3000);
            setTimeout(() => {
                resetPasswordButton.disabled = false;
                resetPasswordButton.classList.remove('opacity-60', 'cursor-not-allowed');
                loadingSpinner.classList.add('hidden');
            }, 3000);
        }
    })
    .catch(error => {
        showToast('danger', 'An error occurred. Please try again later.', 3000);
        console.error('Error:', error);

        setTimeout(() => {
            resetPasswordButton.disabled = false;
            resetPasswordButton.classList.remove('opacity-60', 'cursor-not-allowed');
            loadingSpinner.classList.add('hidden');
        }, 3000);
    });
}