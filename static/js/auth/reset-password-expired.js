document.addEventListener('DOMContentLoaded', function() {
    const resendButton = document.getElementById('resendButton');
    resendButton.addEventListener('click', sendNewResetLink);
});

function sendNewResetLink() {
    const resendButton = document.getElementById('resendButton');
    const email = document.getElementById('emailInput').value.trim();
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

    resendButton.disabled = true;
    resendButton.classList.add('opacity-60', 'cursor-not-allowed');

    

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
            showToast('success', 'A new password reset link has been sent to your email.', 3000);
        } else {
            showToast('danger', data.message || 'Failed to send reset link. Please try again.', 5000);

            setTimeout(() => {
                resendButton.disabled = false;
                resendButton.classList.remove('opacity-60', 'cursor-not-allowed');
            }, 3000);

        }
    })
    .catch(error => {
        showToast('danger', 'An error occurred. Please try again later.', 3000);
        console.error('Error:', error);

        setTimeout(() => {
            resendButton.disabled = false;
            resendButton.classList.remove('opacity-60', 'cursor-not-allowed');
        }, 3000);
    });
}
