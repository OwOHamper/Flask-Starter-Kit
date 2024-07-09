document.addEventListener('DOMContentLoaded', function() {
    const resetPasswordButton = document.getElementById('resetPasswordButton');
    resetPasswordButton.addEventListener('click', validateAndSubmit);
});

function validateAndSubmit() {
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirm-password').value;
    const token = document.getElementById('token').value;
    const csrfToken = document.getElementById('csrf').value;

    if (password === '') {
        showToast('danger', 'Please enter a new password.', 3000);
        return;
    }

    const passwordError = validatePassword(password);
    if (passwordError) {
        showToast('danger', passwordError, 3000);
        return;
    }

    if (confirmPassword === '') {
        showToast('danger', 'Please confirm your new password.', 3000);
        return;
    }

    if (password !== confirmPassword) {
        showToast('danger', 'Passwords do not match.', 3000);
        return;
    }

    // Add any additional password strength checks here

    // If all validations pass, submit the data
    fetch('/reset-password', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            "password": password,
            "confirm_password": confirmPassword,
            "token": token,
            "_csrf_token": csrfToken
        }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('success', 'Password reset successful!', 3000);
            // Redirect to login page after successful reset
            setTimeout(() => {
                window.location.href = '/login';
            }, 1000);
        } else {
            showToast('danger', data.message || 'Password reset failed. Please try again.', 3000);
        }
    })
    .catch(error => {
        showToast('danger', 'An error occurred. Please try again later.', 3000);
        console.error('Error:', error);
    });
}

function validatePassword(password) {
    if (password.length < 8) {
        return "Password must be at least 8 characters long.";
    }
    if (!/[A-Z]/.test(password)) {
        return "Password must contain at least one uppercase letter.";
    }
    if (!/[a-z]/.test(password)) {
        return "Password must contain at least one lowercase letter.";
    }
    if (!/\d/.test(password)) {
        return "Password must contain at least one number.";
    }
    if (!/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)) {
        return "Password must contain at least one special character.";
    }
    return null; // Password passes all checks
}