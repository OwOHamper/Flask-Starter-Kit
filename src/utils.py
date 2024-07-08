import re

def validate_password(password):
    if len(password) < 8:
        return "Password must be at least 8 characters long."
    if not re.search(r'[A-Z]', password):
        return "Password must contain at least one uppercase letter."
    if not re.search(r'[a-z]', password):
        return "Password must contain at least one lowercase letter."
    if not re.search(r'\d', password):
        return "Password must contain at least one number."
    if not re.search(r"""[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]""", password):
        return "Password must contain at least one special character."
    return None  # Password passes all checks

def validate_email(email):
    if re.search(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
        return True
    else:
        return False