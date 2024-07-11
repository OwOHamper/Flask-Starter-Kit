
import uuid, logging
from datetime import datetime, timezone

from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, g
from flask_login import login_user, logout_user, current_user

from src import config
from src.localization import get_locale
from src.extensions import limiter, bcrypt, mongo

from src.blueprints.auth.auth_utils import validate_email, validate_password, rate_limit_exceeded, build_user, User

from src.blueprints.auth.verify_email import send_verification_email, verify_email_bp
from src.blueprints.auth.password_reset import password_reset_bp
from src.blueprints.auth.oauth import oauth_bp

auth = Blueprint('auth', __name__)

auth.register_blueprint(verify_email_bp)
auth.register_blueprint(password_reset_bp)
auth.register_blueprint(oauth_bp)
    



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
        'alternative_id': alternative_id,
        'auth_provider': 'local',
        'name': email.split('@')[0]
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
        if user['auth_provider'] != 'local':
            #Provide feedback that this user is already registered with a different provider
            return jsonify({'success': False, 'message': 'An account already exists for this email. Please use your social login method to sign in.'}), 400
        if bcrypt.check_password_hash(user['password'], password): 
            if user['account_status'] != 'active':
                if user['account_status'] == 'deactivated':
                    return jsonify({'success': False, 'message': 'Your account has been deactivated. Please contact support for assistance.'}), 400
                elif user['account_status'] == 'suspended':
                    return jsonify({'success': False, 'message': 'Your account has been suspended. Please contact support for assistance.'}), 400
                else:
                    return jsonify({'success': False, 'message': 'Your account is currently inactive. Please contact support for assistance.'}), 400
            
            elif not user['email_verified']:
                return jsonify({'success': False, 'redirect': url_for('auth.verify_email.verify_email_page', email=email), 'message': 'Please verify your email address to activate your account. Check your inbox for a verification email or request a new one.'}), 400
               
            mongo.db.users.update_one({'email': email},
                {'$set': {
                'last_login': datetime.now(tz=timezone.utc),
                'metadata.last_login_ip': request.remote_addr,
                'metadata.last_login_user_agent': request.headers.get('User-Agent'),
                'security.failed_login_attempts': 0,
                
            },
                 '$inc': {
                'usage_stats.total_logins': 1
            }})
            
            
            additional_data = {}
            if session.get('next'):
                additional_data['redirect'] = session.get('next')
            
            
            userObject = User(user['alternative_id'])
            
            session.clear()
            session.permanent = remember
            
            g.set_lang_cookie = True
            g.lang = user['preferences']['language']
            
            login_user(userObject, remember=remember)

                
            logging.info(f"Additional data: {additional_data}")

            return jsonify({'success': True, 'message': 'User logged in successfully!'} | additional_data), 200
        else:
            mongo.db.users.update_one({'email': email}, {'$inc': {
                'security.failed_login_attempts': 1,
                'usage_stats.total_failed_logins': 1
                }})
        
    return jsonify({'success': False, 'message': 'Incorrect email or password.'}), 401


@auth.route("/logout")
@limiter.limit("20 per minute", on_breach=lambda limit: rate_limit_exceeded('auth.logout'))
def logout():
    logout_user()
    return redirect(url_for('pages.home'))
