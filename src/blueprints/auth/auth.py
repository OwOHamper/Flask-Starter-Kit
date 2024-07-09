
import uuid, logging, time
from datetime import datetime, timezone, timedelta

from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash, make_response
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message

from src import config
from src.localization import get_locale
from src.extensions import limiter, bcrypt, mongo, login_manager, serializer, mail
from src.utils import validate_email, validate_password, rate_limit_exceeded, build_user

from src.blueprints.auth.verify_email import send_verification_email, verify_email_bp

auth = Blueprint('auth', __name__)

auth.register_blueprint(verify_email_bp)
    



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
        return redirect('/you-are-authenticated-log-out-first')

    return render_template('pages/auth/login.html', locale=get_locale())

@auth.route('/register')
@auth.route('/signup')
def register():
    if current_user.is_authenticated:
        return redirect('/you-are-authenticated-log-out-first')
    return render_template('pages/auth/registration.html', locale=get_locale())


@auth.route('/forgot-password')
def forgot_password():
    return render_template('pages/auth/forgot-password.html', locale=get_locale())



@auth.route("/forgot-password", methods=["POST"])
@limiter.limit("5 per hour", on_breach=lambda limit: rate_limit_exceeded('auth.forgot_password'))
def forgot_password_post():
    email = request.json.get('email')
    
    if not email or not isinstance(email, str) or not validate_email(email):
        return jsonify({'success': False, 'message': 'Valid email is required.'}), 400
    
    user = mongo.db.users.find_one({'email': email})
    
    if user:
        token = serializer.dumps(email, salt='password-reset-salt')
        reset_url = url_for('auth.reset_password', token=token, _external=True)
        
        html = render_template('emails/reset-password.html', reset_url=reset_url)
        
        msg = Message('Reset Your Password',
                      sender=config.MAIL_DEFAULT_SENDER,
                      recipients=[email])
        msg.html = html
        
        mail.send(msg)
        
        mongo.db.users.update_one(
            {'email': email},
            {'$set': {
                'security.password_reset_token': token,
                'security.password_reset_token_expires': datetime.now(tz=timezone.utc) + timedelta(hours=1)
            }}
        )
    
    # Always return a success message to prevent user enumeration
    return jsonify({'success': True, 'message': 'A password reset email has been sent.'}), 200

@auth.route('/reset-password/<token>', methods=['GET'])
@limiter.limit("15 per hour", on_breach=lambda limit: rate_limit_exceeded('auth.reset_password'))
def reset_password(token):
    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=3600)
    except:
        return render_template('pages/auth/reset-password-error.html', locale=get_locale())

    user = mongo.db.users.find_one({'email': email})
    if not user or user['security']['password_reset_token'] != token:
        return render_template('pages/auth/reset-password-error.html', locale=get_locale())

    return render_template('pages/auth/reset-password.html', locale=get_locale(), token=token)

@auth.route('/reset-password', methods=['POST'])
@limiter.limit("15 per hour", on_breach=lambda limit: rate_limit_exceeded('auth.reset_password_post'))
def reset_password_post():
    password = request.json.get('password')
    confirm_password = request.json.get('confirm_password')
    token = request.json.get('token')
    
    if not password or not confirm_password or not token:
        return jsonify({'success': False, 'message': 'Password, confirm_password and token are required'}), 400
    
    if type(password) != str or type(confirm_password) != str or type(token) != str:
        return jsonify({'success': False, 'message': 'password, confirm_password and tokenmust be strings.'}), 400
    
    if password != confirm_password:
        return jsonify({'success': False, 'message': 'Passwords do not match.'}), 400
    
    password_error = validate_password(password)
    if password_error:
        return jsonify({'success': False, 'message': password_error}), 400
    
    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=3600)
    except:
        return jsonify({'success': False, 'message': 'Your password reset link has expired or is invalid. Please request a new one.'}), 400

    user = mongo.db.users.find_one({'email': email})
    if not user or user['security']['password_reset_token'] != token:
        return jsonify({'success': False, 'message': 'Your password reset link has expired or is invalid. Please request a new one.'}), 400



    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    alternate_id = str(uuid.uuid4())
    
    mongo.db.users.update_one(
        {'email': email},
        {
            '$set': {
                'password': hashed_password,
                'alternative_id': alternate_id,
                'updated_at': datetime.now(tz=timezone.utc),
                'security.failed_login_attempts': 0,
                'security.password_reset_token': None,
                'security.password_reset_token_expires': None,
                'security.last_password_change': datetime.now(tz=timezone.utc)
            }
        }
    )

    return jsonify({'success': True, 'message': 'Your password has been successfully reset. You can now log in with your new password.'}), 200


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
            mongo.db.users.update_one({'email': email}, {'$set': {
                'last_login': datetime.now(tz=timezone.utc),
                'metadata.last_login_ip': request.remote_addr,
                'metadata.last_user_agent': request.headers.get('User-Agent'),
                'security.failed_login_attempts': 0
            }})
            
            
            user = User(user['alternative_id'])
            
            session.clear()
            session.permanent = remember
            
            login_user(user, remember=remember)

            return jsonify({'success': True, 'message': 'User logged in successfully!'}), 200
        else:
            mongo.db.users.update_one({'email': email}, {'$inc': {'security.failed_login_attempts': 1}})
        
    return jsonify({'success': False, 'message': 'Incorrect email or password.'}), 401


@auth.route("/logout")
@limiter.limit("20 per minute", on_breach=lambda limit: rate_limit_exceeded('auth.logout'))
def logout_post():
    logout_user()
    return jsonify({'success': True, 'message': 'User logged out successfully!'}), 200
