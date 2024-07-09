import logging, uuid
from datetime import datetime, timezone, timedelta

from flask import Blueprint, render_template, request, jsonify, url_for
from flask_mail import Message

from src.extensions import limiter, mongo, serializer, mail, bcrypt
from src.utils import validate_email, rate_limit_exceeded, validate_password
from src.localization import get_locale
from src import config

password_reset_bp = Blueprint('password_reset', __name__)


@password_reset_bp.route('/forgot-password')
def forgot_password():
    return render_template('pages/auth/forgot-password.html', locale=get_locale())



@password_reset_bp.route("/forgot-password", methods=["POST"])
@limiter.limit("5 per hour", on_breach=lambda limit: rate_limit_exceeded('auth.password_reset.forgot_password'))
def forgot_password_post():
    email = request.json.get('email')
    
    if not email or not isinstance(email, str) or not validate_email(email):
        return jsonify({'success': False, 'message': 'Valid email is required.'}), 400
    
    user = mongo.db.users.find_one({'email': email})
    
    if user:
        token = serializer.dumps(email, salt='password-reset-salt')
        reset_url = url_for('auth.password_reset.reset_password', token=token, _external=True)
        
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

@password_reset_bp.route('/reset-password/<token>', methods=['GET'])
@limiter.limit("15 per hour", on_breach=lambda limit: rate_limit_exceeded('auth.password_reset.reset_password'))
def reset_password(token):
    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=3600)
    except:
        return render_template('pages/auth/reset-password-error.html', locale=get_locale())

    user = mongo.db.users.find_one({'email': email})
    if not user or user['security']['password_reset_token'] != token:
        return render_template('pages/auth/reset-password-error.html', locale=get_locale())

    return render_template('pages/auth/reset-password.html', locale=get_locale(), token=token)

@password_reset_bp.route('/reset-password', methods=['POST'])
@limiter.limit("15 per hour", on_breach=lambda limit: rate_limit_exceeded('auth.password_reset.reset_password_post'))
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
