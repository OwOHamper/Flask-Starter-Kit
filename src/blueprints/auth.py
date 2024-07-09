
import uuid, logging
from datetime import datetime, timezone

from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash, make_response
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
    logging.info(f"Sending verification email to {user_email}")
    token = serializer.dumps(user_email, salt='email-verify-salt')
    
    verify_url = url_for('auth.verify_email', token=token, _external=True)
    
    html = render_template('emails/verify-email.html', verification_url=verify_url)
    
    msg = Message('Verify Your Email',
                  sender=config.MAIL_DEFAULT_SENDER,
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


def rate_limit_exceeded(route_name=None):
    base_message = "You've made too many requests in a short time. Please wait a moment and try again."
    
    route_specific_messages = {
        "auth.login": "Too many login attempts. Please wait a moment before trying again.",
        "auth.register": "We've received too many registration requests. Please try again in a few minutes.",
        "auth.resend_verification_email": "You've requested too many verification emails. Please check your inbox and try again later."
    }
    
    message = route_specific_messages.get(route_name, base_message)
    
    if route_name == "auth.verify_email":
        return make_response(render_template('pages/auth/email-verified.html', locale=get_locale(), success=False))
    
    return make_response(jsonify({'success': False, 'message': message}), 429)


@auth.route('/login')
def login():
    if current_user.is_authenticated:
        return redirect('/you-are-authenticated-log-out-first')

    return render_template('pages/auth/login.html', locale=get_locale())

@auth.route('/register')
@auth.route('/signup')
def register():
    if current_user.is_authenticated:
        return redirect('/you-are-authenticated-log-out-first')
    return render_template('pages/auth/registration.html', locale=get_locale())

@auth.route('/verify-email')
def verify_email_page():
    email = request.args.get('email')
    if not email:
        return render_template('pages/auth/verify-email.html', locale=get_locale())
    return render_template('pages/auth/verify-email.html', locale=get_locale(), email=email)

@auth.route('/verify-email/<token>')
@limiter.limit("25 per hour; 125 per day", on_breach=lambda limit: rate_limit_exceeded('auth.verify_email'))
def verify_email(token):
    try:
        email = serializer.loads(token, salt='email-verify-salt', max_age=3600)  # Token expires after 1 hour
    except:
        return render_template('pages/auth/email-verified.html', locale=get_locale(), success=False)
    
    user = mongo.db.users.find_one({'email': email})
    if user:
        mongo.db.users.update_one({'email': email}, {'$set': {'email_verified': True}})
        return render_template('pages/auth/email-verified.html', locale=get_locale(), success=True)
    else:
        return render_template('pages/auth/email-verified.html', locale=get_locale(), success=False)


@auth.route('/resend-verification-email', methods=['POST'])
@limiter.limit("5 per hour", on_breach=lambda limit: rate_limit_exceeded('auth.resend_verification_email'))
def resend_verification_email():
    email = request.json.get('email')
    
    if not email or not isinstance(email, str) or not validate_email(email):
        return jsonify({'success': False, 'message': 'Valid email is required.'}), 400
    
    
    user = mongo.db.users.find_one({'email': email})
    
    if not user:
        return jsonify({'success': False, 'message': 'User with that email does not exist.'}), 400
    
    if user['email_verified'] == False:
        send_verification_email(email)
        return jsonify({'success': True, 'message': 'Verification email sent. Please check your inbox.'}), 200
    else:
        return jsonify({'success': False, 'message': 'This email address is already verified.'}), 400

@limiter.limit("5 per minute; 50 per day", on_breach=lambda limit: rate_limit_exceeded('auth.register'))
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
    #Preventing user enumeration on used email is way too hardcode
    if existing_user:    
        return jsonify({'success': False, 'message': 'User with that email already exists.'}), 400
    
    password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    alternative_id = str(uuid.uuid4())
    
    
    mongo.db.users.insert_one(build_user({
        'email': email,
        'password_hash': password_hash,
        'alternative_id': alternative_id
    }))
    
    send_verification_email(email)
            
    
    return jsonify({'success': True, 'message': 'User registered successfully!'}), 200
    
    

@auth.route("/login", methods=["POST"])
@limiter.limit("10 per minute; 200 per day", on_breach=lambda limit: rate_limit_exceeded('auth.login'))
def login_post():
    if current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'You are already logged in.'}), 400
        
    email = request.json.get('email')
    password = request.json.get('password')
    remember = request.json.get('remember')
    
    if not email or not password or remember == None:
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
@limiter.limit("20 per minute", on_breach=lambda limit: rate_limit_exceeded('auth.logout'))
def logout_post():
    logout_user()
    return jsonify({'success': True, 'message': 'User logged out successfully!'}), 200
