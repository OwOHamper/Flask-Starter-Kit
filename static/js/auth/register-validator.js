document.getElementById('signupForm').addEventListener('submit', function(event) {
    event.preventDefault();
    // Reset error messages
    document.getElementById('emailError').textContent = '';
    document.getElementById('passwordError').textContent = '';
    document.getElementById('confirmPasswordError').textContent = '';

    // Validate email
    const email = document.getElementById('email');
    if (!email.validity.valid) {
        document.getElementById('emailError').textContent = 'Please enter a valid email address.';
        return;
    }

    // Validate password
    const password = document.getElementById('password');
    if (password.value.length < 8) {
        document.getElementById('passwordError').textContent = 'Password must be at least 8 characters long.';
        return;
    }

    // Check password strength
    if (!/(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*[!@#$%^&*])/.test(password.value)) {
        document.getElementById('passwordError').textContent = 'Password must include at least one uppercase letter, one lowercase letter, one number, and one special character.';
        return;
    }

    // Validate password confirmation
    const confirmPassword = document.getElementById('confirm-password');
    if (password.value !== confirmPassword.value) {
        document.getElementById('confirmPasswordError').textContent = 'Passwords do not match.';
        return;
    }

    // If all validations pass, you can submit the form
    // For now, we'll just log a success message
    console.log('Form submitted successfully');
});