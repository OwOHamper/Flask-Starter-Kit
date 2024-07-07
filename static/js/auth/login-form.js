document.addEventListener('DOMContentLoaded', function() {
    const loginButton = document.getElementById('loginButton');
    loginButton.addEventListener('click', validateAndSubmit);
});

function validateAndSubmit() {
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    const rememberMe = document.getElementById('remember').checked;
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

    // If all validations pass, show success message and submit the data
    showToast('success', 'Logging in...', 3000);
    
    // Use fetch to send the data to the server
    fetch('/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            "email": email,
            "password": password,
            "remember": rememberMe,
            "_csrf_token": csrfToken
        }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('success', 'Login successful!', 3000);
            // Redirect or update UI as needed
            setTimeout(() => {
                window.location.href = '/';  // Adjust as needed
            }, 1000);
        } else {
            showToast('danger', data.message || 'Login failed. Please try again.', 3000);
        }
    })
    .catch(error => {
        showToast('danger', 'An error occurred. Please try again later.', 3000);
        console.error('Error:', error);
    });
}