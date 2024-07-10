document.addEventListener('DOMContentLoaded', function() {
    const linkButton = document.getElementById('linkButton');
    linkButton.addEventListener('click', linkAccount);
});

function linkAccount() {
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
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

    
    // Use fetch to send the data to the server
    fetch('/link-account', {
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
            showToast('success', 'Account linked successfully. Redirecting...', 3000);
            // Redirect or update UI as needed
            // if redirect field in data is set, redirect to that path
            let redirect = data.redirect || '/';
            setTimeout(() => {
                window.location.href = redirect;
            }, 1000);
        } else {
            if (data.redirect) {
                setTimeout(() => {
                    window.location.href = data.redirect;
                }, 0);
            }
            showToast('danger', data.message || 'Login failed. Please try again.', 5000);
        }
    })
    .catch(error => {
        showToast('danger', 'An error occurred. Please try again later.', 3000);
        console.error('Error:', error);
    });
}