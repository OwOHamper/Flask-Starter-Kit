document.addEventListener('DOMContentLoaded', function() {
    const resendButton = document.getElementById('resendButton');
    const timerCircle = document.getElementById('timerCircle');
    const timerText = document.getElementById('timerText');
    const timerContainer = document.getElementById('timerContainer');
    const emailInput = document.getElementById('emailInput');

    const totalTime = 60;
    let countdown = totalTime;
    if (document.getElementById('verification-failed') !== null) {
        countdown = 5;
    }
    updateButtonState();

    function updateButtonState() {
        if (countdown > 0) {
            resendButton.disabled = true;
            resendButton.classList.add('opacity-60', 'cursor-not-allowed');
            timerContainer.classList.remove('hidden');
            
            const progress = (countdown / totalTime) * 100;
            timerCircle.style.strokeDashoffset = 100 - progress;
            timerText.textContent = `${countdown}s`;
            
            countdown--;
            setTimeout(updateButtonState, 1000);
        } else {

            timerCircle.style.strokeDashoffset = 0;
            timerText.textContent = '0s';

            resendButton.disabled = false;
            resendButton.classList.remove('opacity-60', 'cursor-not-allowed');
            // timerContainer.classList.add('hidden');
            resendButton.addEventListener('click', resendVerificationEmail);
        }
    }

    function resendVerificationEmail() {
        const email = emailInput.value.trim();
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
                showToast('success', 'Verification email resent. Please check your inbox.', 3000);
                startResendCooldown();
            } else {
                showToast('danger', data.message || 'Failed to resend verification email. Please try again.', 3000);
            }
        })
        .catch(error => {
            showToast('danger', 'An error occurred. Please try again later.', 3000);
            console.error('Error:', error);
        });
    }

    function startResendCooldown() {
        countdown = totalTime;
        updateButtonState();
    }
});
