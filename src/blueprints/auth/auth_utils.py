import re, logging
from flask import request, make_response, render_template, jsonify
from datetime import datetime, timezone


from src.extensions import mongo, login_manager
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
    


def build_user(user_data):
    if user_data.get('oauth_login') == True:
        total_logins = 1
        verification_emails_sent = 0
        email_verified = True
        last_login = datetime.now(tz=timezone.utc)
        last_login_ip = request.remote_addr
        
    else:
        total_logins = 0
        verification_emails_sent = 1
        email_verified = False
        last_login = None
        last_login_ip = None
    
    return {
        'email': user_data.get('email').lower(),
        'password': user_data.get('password_hash'),
        'alternative_id': user_data.get('alternative_id'),
        'created_at': datetime.now(tz=timezone.utc),
        'updated_at': datetime.now(tz=timezone.utc),
        'last_login': last_login,
        'email_verified': email_verified,
        'roles': ['user'],
        'profile': {
            'profile_picture': user_data.get('profile_picture'),
            'name': user_data.get('name'),
            'bio': user_data.get('bio')
        },  
        'preferences': {
            'language': get_locale()
        },
        'security': {
            'failed_login_attempts': 0,
            'last_password_change': None,
            'password_reset_token': None,
            'password_reset_token_expires': None,
            'two_factor_enabled': False
        },
        'auth_provider': user_data.get('auth_provider'),
        'connections': user_data.get('connections', {}), # For OAuth logins
        'account_status': 'active',  # Can be 'active', 'suspended', 'deactivated'
        'metadata': {
            'registration_ip': request.remote_addr,
            'last_login_ip': last_login_ip,
            'last_login_user_agent': request.headers.get('User-Agent')
        },
        'usage_stats': {
            'total_logins': total_logins,
            'total_failed_logins': 0,
            'total_password_resets': 0,
            'total_verification_emails_sent': verification_emails_sent # The first verification email is sent during registration
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

#USE of alternative id instead of user id, so login can be invalidated without changing the user id
class User():
    def __init__(self, alternative_id, is_active_variable=True, additional_user_data_variable={}):
        self.id = alternative_id
        self.is_active_variable = is_active_variable
        
        self.additional_user_data_variable = additional_user_data_variable
        
        
    @property
    def additional_user_data(self):
        return self.additional_user_data_variable
        
    @property
    def is_active(self):
        return self.is_active_variable
    
    @property
    def is_authenticated(self):
        return self.is_active
    
    @property
    def is_anonymous(self):
        return False
    
    def get_id(self):
        return self.id
    
    
@login_manager.user_loader
def load_user(alternative_id):
    user_data = mongo.db.users.find_one({'alternative_id': alternative_id})
    if user_data:
        is_active = user_data['account_status'] == 'active' and user_data['email_verified']

        additional_user_data = {
            'email': user_data['email'],
            'profile_picture': user_data['profile']['profile_picture'],
            'name': user_data['profile']['name'],
            'roles': user_data['roles']
        }
        
        return User(user_data['alternative_id'], is_active_variable=is_active, additional_user_data_variable=additional_user_data)
    return None