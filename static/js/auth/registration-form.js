document.addEventListener('DOMContentLoaded', function() {
    const registerButton = document.getElementById('registerButton');
    registerButton.addEventListener('click', validateAndSubmit);
});

function validateAndSubmit() {
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirm-password').value;
    const termsCheckbox = document.getElementById('terms');
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

    if (password === '') {
        showToast('danger', 'Please enter your password.', 3000);
        return;
    }

    const passwordError = validatePassword(password);
    if (passwordError) {
        showToast('danger', passwordError, 3000);
        return;
    }

    if (password !== confirmPassword) {
        showToast('danger', 'Passwords do not match.', 3000);
        return;
    }

    if (!termsCheckbox.checked) {
        showToast('danger', 'Please accept the Terms and Conditions and Privacy Policy.', 3000);
        return;
    }

    // If all validations pass, show success message and submit the data
    // showToast('success', 'Creating your account...', 3000);
    
    // Use fetch to send the data to the server
    fetch('/register', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            "email": email,
            "password": password,
            "_csrf_token": csrfToken
        }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('success', data.message, 3000);
            document.getElementById('email').value = '';
            document.getElementById('password').value = '';
            document.getElementById('confirm-password').value = '';
            document.getElementById('terms').checked = false;
            // Redirect or update UI as needed
            setTimeout(() => {
                window.location.href = '/login';  // Adjust as needed
            }, 1000);
        } else {
            showToast('danger', data.message || 'Registration failed. Please try again.', 3000);
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