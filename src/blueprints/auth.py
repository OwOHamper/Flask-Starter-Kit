from flask import Blueprint, render_template, request, jsonify, session
import re
from src.localization import get_locale

import uuid

from flask_login import UserMixin, login_user, logout_user, login_required, current_user

# from server import mongo
from src.extensions import limiter, bcrypt, mongo, login_manager

auth = Blueprint('auth', __name__)





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
    user_data = mongo.db.users.find_one({'alternative_id': alternative_id})
    if user_data:
        return User(user_data['alternative_id'])
    return None

# @auth.record_once
# def on_load(state):
    
    # auth.mongo = state.options.get('mongo').db
    # auth.bcrypt = state.options.get('bcrypt')

@auth.route('/login')
def login():
    return render_template('pages/auth/login.html', locale=get_locale())

@auth.route('/register')
@auth.route('/signup')
def register():
    return render_template('pages/auth/registration.html', locale=get_locale())


@limiter.limit("5 per minute; 50 per day")
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
    
    
    existing_user = mongo.db.users.find_one({'email': email})
    #PREVENTS USER ENUMERATION ATTACKS, by not letting attacker/user know where account with that email exists
    if not existing_user:    
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        alternative_id = str(uuid.uuid4())
        
        user_id = mongo.db.users.insert_one({
            'email': email,
            'password': password_hash,
            'alternative_id': alternative_id
        }).inserted_id
    
    
    return jsonify({'success': True, 'message': 'User registered successfully!'}), 200
    
    
@limiter.limit("10 per minute; 200 per day")
@auth.route("/login", methods=["POST"])
def login_post():
    email = request.json.get('email')
    password = request.json.get('password')
    remember = request.json.get('remember')
    
    user = mongo.db.users.find_one({'email': email})
    if user:
        if bcrypt.check_password_hash(user['password'], password):    
            user = User(user['alternative_id'])
            
            session.clear()
            session.permanent = remember
            
            login_user(user, remember=remember)

            return jsonify({'success': True, 'message': 'User logged in successfully!'}), 200
        
    return jsonify({'success': False, 'message': 'Incorrect email or password.'}), 401

@limiter.limit("20 per minute")
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