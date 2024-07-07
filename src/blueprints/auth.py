from flask import Blueprint, render_template, url_for, request, redirect, jsonify
import re
from src.localization import get_locale

import uuid

from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user


auth = Blueprint('auth', __name__)

login_manager = LoginManager()
login_manager.login_view = 'auth.login'


#USE of alternative id instead of user id, so login can be invalidated without changing the user id
class User():
    def __init__(self, alternative_id):
        self.id = alternative_id
        
    def is_active(self):
        return True
    
    def is_authenticated(self):
        return True
    
    def is_anonymous(self):
        return False
    
    def get_id(self):
        return self.id

@login_manager.user_loader
def load_user(alternative_id):
    user_data = auth.mongo.users.find_one({'alternative_id': alternative_id})
    if user_data:
        return User(user_data['alternative_id'])
    return None

@auth.record_once
def on_load(state):
    auth.mongo = state.options.get('mongo').db
    auth.bcrypt = state.options.get('bcrypt')

@auth.route('/login')
def login():
    return render_template('pages/auth/login.html', locale=get_locale())

@auth.route('/register')
@auth.route('/signup')
def register():
    return render_template('pages/auth/registration.html', locale=get_locale())



@auth.route("/register", methods=["POST"])
@auth.route("/signup", methods=["POST"])
def register_post():
    email = request.json.get('email')
    password = request.json.get('password')
    
    if not validate_email(email):
        return jsonify({'success': False, 'message': 'Invalid email address.'}), 400
    
    password_error = validate_password(password)
    if password_error:
        return jsonify({'success': False, 'message': password_error}), 400
    
    
    existing_user = auth.mongo.users.find_one({'email': email})
    if existing_user:
        return jsonify({'success': False, 'message': 'User with that email already exists.'}), 400
    
    password_hash = auth.bcrypt.generate_password_hash(password).decode('utf-8')
    alternative_id = str(uuid.uuid4())
    
    user_id = auth.mongo.users.insert_one({
        'email': email,
        'password': password_hash,
        'alternative_id': alternative_id
    }).inserted_id
    
    
    return jsonify({'success': True, 'message': 'User registered successfully!'}), 200
    
    

@auth.route("/login", methods=["POST"])
def login_post():
    email = request.json.get('email')
    password = request.json.get('password')
    remember = request.json.get('remember')
    
    user = auth.mongo.users.find_one({'email': email})
    if not user:
        return jsonify({'success': False, 'message': 'User with that email does not exist.'}), 400
    
    if not auth.bcrypt.check_password_hash(user['password'], password):
        return jsonify({'success': False, 'message': 'Incorrect password.'}), 401
    
    user = User(user['alternative_id'])
    login_user(user, remember=remember)

    return jsonify({'success': True, 'message': 'User logged in successfully!'}), 200

@auth.route("/logout")
def logout_post():
    logout_user()
    return jsonify({'success': True, 'message': 'User logged out successfully!'}), 200


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