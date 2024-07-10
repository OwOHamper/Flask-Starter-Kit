from flask import make_response, render_template, jsonify, request
from datetime import datetime, timezone, timedelta
import re

from src.localization import get_locale

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
    
    
class ProxyFix:
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        
        if 'HTTP_X_FORWARDED_SCHEME' in environ:
            environ['wsgi.url_scheme'] = environ['HTTP_X_FORWARDED_SCHEME']

        if 'HTTP_X_REAL_IP' in environ:
            environ['REMOTE_ADDR'] = environ['HTTP_X_REAL_IP']

        return self.app(environ, start_response)
    
def build_user(user_data):
    return {
        'email': user_data.get('email').lower(),
        'password': user_data.get('password_hash'),
        'alternative_id': user_data.get('alternative_id'),
        'created_at': datetime.now(tz=timezone.utc),
        'updated_at': datetime.now(tz=timezone.utc),
        'last_login': None,
        'email_verified': False,
        'roles': ['user'],
        'profile': {
            'profile_picture': None,
            'display_name': user_data.get('email').split('@'),
            'bio': None
        },  
        'preferences': {
            'language': get_locale()
        },
        'security': {
            'failed_login_attempts': 0,
            'last_password_change': datetime.now(tz=timezone.utc),
            'password_reset_token': None,
            'password_reset_token_expires': None,
            'two_factor_enabled': False
        },
        'connections': {},
        'account_status': 'active',  # Can be 'active', 'suspended', 'deactivated'
        'metadata': {
            'registration_ip': request.remote_addr,
            'last_login_ip': None,
            'last_user_agent': request.headers.get('User-Agent')
        },
        'usage_stats': {
            'total_logins': 0,
            'total_failed_logins': 0,
            'total_password_resets': 0,
            'total_verification_emails_sent': 1 # The first verification email is sent during registration
        }
            
    }
    
    
def rate_limit_exceeded(route_name=None):
    base_message = "You've made too many requests in a short time. Please wait a moment and try again."
    
    route_specific_messages = {
        "auth.login": "Too many login attempts. Please wait a moment before trying again.",
        "auth.register": "We've received too many registration requests. Please try again in a few minutes.",
        "auth.resend_verification_email": "You've requested too many verification emails. Please check your inbox and try again later.",
        "auth.forgot_password": "Too many password reset requests. For security reasons, please wait before trying again.",
        "auth.reset_password_post": "Too many password reset requests. For security reasons, please wait before trying again."
    }
    
    message = route_specific_messages.get(route_name, base_message)
    
    if route_name == "auth.verify_email":
        return make_response(render_template('pages/auth/email-verified.html', locale=get_locale(), success=False))
    elif route_name == "auth.reset_password":
        return make_response(render_template('pages/auth/reset-password-error.html', locale=get_locale()))
    
    return make_response(jsonify({'success': False, 'message': message}), 429)