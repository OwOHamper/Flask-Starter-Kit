document.addEventListener('DOMContentLoaded', function() {
    const resendButton = document.getElementById('resendButton');
    resendButton.addEventListener('click', resendVerificationEmail);
});

function resendVerificationEmail() {
    const resendButton = document.getElementById('resendButton');
    resendButton.disabled = true;
    resendButton.classList.add('opacity-60', 'cursor-not-allowed');
    let btnEnableTimeout = setTimeout(() => {
        resendButton.disabled = false;
        resendButton.classList.remove('opacity-60', 'cursor-not-allowed');
    }, 5000);

    const email = document.getElementById('email').value.trim();
    const csrfToken = document.getElementById('csrf').value;


    

    fetch('/resend-verification-email', {
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
            clearTimeout(btnEnableTimeout);
            resendButton.disabled = true;
            resendButton.classList.add('opacity-60', 'cursor-not-allowed');

            setTimeout(() => {
                resendButton.disabled = false;
                resendButton.classList.remove('opacity-60', 'cursor-not-allowed');
            }, 60000);

            showToast('success', 'Verification email resent. Please check your inbox.', 3000);
            
        } else {

            showToast('danger', data.message || 'Failed to resend verification email. Please try again.', 3000);
        }
    })
    .catch(error => {

        showToast('danger', 'An error occurred. Please try again later.', 5000);
        console.error('Error:', error);
    });
}