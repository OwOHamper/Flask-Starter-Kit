
import uuid
from datetime import datetime, timezone

from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message

from src import config
from src.localization import get_locale
from src.extensions import limiter, bcrypt, mongo, login_manager, serializer, mail
from src.utils import validate_email, validate_password

auth = Blueprint('auth', __name__)



def build_user(user_data):
    return {
        'email': user_data.get('email'),
        'password': user_data.get('password_hash'),
        'alternative_id': user_data.get('alternative_id'),
        'created_at': datetime.now(tz=timezone.utc),
        'updated_at': datetime.now(tz=timezone.utc),
        'is_active': True,
        'last_login': None,
        'email_verified': False,
        'roles': ['user'],
        'profile': {
            'profile_picture': None,
        },  
        'preferences': {
            'language': get_locale()
        },
        'security': {
            'failed_login_attempts': 0,
            'last_password_change': None,
            'password_reset_token': None,
            'password_reset_token_expires': None
        },
        'connections': {},
        'account_status': 'active',  # Can be 'active', 'suspended', 'deactivated'
        'metadata': {
            'registration_ip': request.remote_addr,
            'last_login_ip': None,
            'user_agent': request.headers.get('User-Agent')
        }
    }
    
    
def send_verification_email(user_email):
    token = serializer.dumps(user_email, salt='email-verify-salt')
    
    verify_url = url_for('auth.verify_email', token=token, _external=True)
    
    html = render_template('emails/verify-email.html', verification_url=verify_url)
    
    msg = Message('Verify Your Email',
                  recipients=[user_email])
    
    msg.html = html
    
    mail.send(msg)



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


@auth.route('/login')
def login():
    if current_user.is_authenticated:
        return redirect('/')

    return render_template('pages/auth/login.html', locale=get_locale())

@auth.route('/register')
@auth.route('/signup')
def register():
    if current_user.is_authenticated:
        return redirect('/')
    return render_template('pages/auth/registration.html', locale=get_locale())

@auth.route('/verify-email')
def verify_email_page():
    return render_template('pages/auth/verify-email.html', locale=get_locale())

@auth.route('/verify-email/<token>')
@limiter.limit("5 per minute; 50 per day")
def verify_email(token):
    try:
        email = serializer.loads(token, salt='email-verify-salt', max_age=3600)  # Token expires after 1 hour
    except:
        return jsonify({'success': False, 'message': 'The verification link is invalid or has expired.'}), 400
    
    user = mongo.db.users.find_one({'email': email})
    if user:
        mongo.db.users.update_one({'email': email}, {'$set': {'email_verified': True}})
        return jsonify({'success': True, 'message': 'Email verified successfully!'}), 200
    else:
        return jsonify({'success': False, 'message': 'User not found.'}), 404

@auth.route('/resend-verification-email', methods=['POST'])
@limiter.limit("3 per hour")
def resend_verification_email():
    email = request.json.get('email')
    
    if not email or not isinstance(email, str) or not validate_email(email):
        return jsonify({'success': False, 'message': 'Valid email is required.'}), 400
    
    
    user = mongo.db.users.find_one({'email': email})
    

    if user and user['email_verified'] == True:
        send_verification_email(email)
    
    return jsonify({'success': True, 'message': 'If the email exists and is not verified, a verification email has been sent.'}), 200

@limiter.limit("5 per minute; 50 per day")
@auth.route("/register", methods=["POST"])
@auth.route("/signup", methods=["POST"])
def register_post():
    if current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'You are already logged in.'}), 400
    
    email = request.json.get('email')
    password = request.json.get('password')
    terms = request.json.get('terms')
    
    if not email or not password or not terms:
        return jsonify({'success': False, 'message': 'Email and password are required.'}), 400
    
    if type(email) != str or type(password) != str or type(terms) != bool:
        return jsonify({'success': False, 'message': 'Email and password must be strings and terms must be boolean.'}), 400
    
    if not terms:
        return jsonify({'success': False, 'message': 'You must agree to the terms and conditions and Privacy Policy.'}), 400
    
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
        
        
        mongo.db.users.insert_one(build_user({
            'email': email,
            'password_hash': password_hash,
            'alternative_id': alternative_id
        }))
        
        send_verification_email(email)
        
        return redirect(url_for('auth.verify_email_page', email=email))
    
    
    return jsonify({'success': True, 'message': 'User registered successfully!'}), 200
    
    

@auth.route("/login", methods=["POST"])
@limiter.limit("10 per minute; 200 per day")
def login_post():
    if current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'You are already logged in.'}), 400
        
    email = request.json.get('email')
    password = request.json.get('password')
    remember = request.json.get('remember')
    
    if not email or not password or not remember:
        return jsonify({'success': False, 'message': 'Email, password and remember are required.'}), 400
    
    if type(email) != str or type(password) != str or type(remember) != bool:
        return jsonify({'success': False, 'message': 'Email and password must be strings and remember must be boolean.'}), 400
      
    
    
    user = mongo.db.users.find_one({'email': email})
    if user:
        if bcrypt.check_password_hash(user['password'], password):    
            user = User(user['alternative_id'])
            
            session.clear()
            session.permanent = remember
            
            login_user(user, remember=remember)

            return jsonify({'success': True, 'message': 'User logged in successfully!'}), 200
        
    return jsonify({'success': False, 'message': 'Incorrect email or password.'}), 401


@auth.route("/logout")
@limiter.limit("20 per minute")
def logout_post():
    logout_user()
    return jsonify({'success': True, 'message': 'User logged out successfully!'}), 200
