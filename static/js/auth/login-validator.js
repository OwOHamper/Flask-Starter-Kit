document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('loginForm');
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    const emailError = document.getElementById('email_error');
    const passwordError = document.getElementById('password_error');

    function validateEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(String(email).toLowerCase());
    }

    function setValidationState(input, isValid, errorElement) {
        if (isValid) {
            input.classList.remove('border-red-600', 'dark:border-red-500');
            errorElement.classList.add('hidden');
        } else {
            input.classList.add('border-red-600', 'dark:border-red-500');
            errorElement.classList.remove('hidden');
        }
    }

    function validateField(input, validationFunction, errorElement) {
        const isValid = validationFunction(input.value);
        setValidationState(input, isValid, errorElement);
        return isValid;
    }

    emailInput.addEventListener('blur', function() {
        validateField(this, validateEmail, emailError);
    });

    passwordInput.addEventListener('blur', function() {
        validateField(this, (value) => value.length >= 8, passwordError);
    });

    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const isEmailValid = validateField(emailInput, validateEmail, emailError);
        const isPasswordValid = validateField(passwordInput, (value) => value.length >= 8, passwordError);

        if (isEmailValid && isPasswordValid) {
            // Here you would typically send the form data to your server
            console.log('Form is valid. Submitting...');
        } else {
            console.log('Form is invalid. Please correct the errors.');
        }
    });
});