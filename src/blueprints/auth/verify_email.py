import logging


from flask import Blueprint, render_template, request, jsonify, url_for
from flask_mail import Message

from src.extensions import limiter, mongo, serializer, mail
from src.utils import validate_email, rate_limit_exceeded
from src.localization import get_locale
from src import config

verify_email_bp = Blueprint('verify_email', __name__)


def send_verification_email(user_email):
    logging.info(f"Sending verification email to {user_email}")
    token = serializer.dumps(user_email, salt='email-verify-salt')
    
    verify_url = url_for('auth.verify_email.verify_email', token=token, _external=True)
    
    html = render_template('emails/verify-email.html', verification_url=verify_url)
    
    msg = Message('Verify Your Email',
                  sender=config.MAIL_DEFAULT_SENDER,
                  recipients=[user_email])
    
    msg.html = html
    
    mail.send(msg)

@verify_email_bp.route('/verify-email')
def verify_email_page():
    email = request.args.get('email')
    if not email:
        return render_template('pages/auth/verify-email.html', locale=get_locale())
    return render_template('pages/auth/verify-email.html', locale=get_locale(), email=email)


@verify_email_bp.route('/verify-email/<token>')
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


@verify_email_bp.route('/resend-verification-email', methods=['POST'])
@limiter.limit("15 per hour", on_breach=lambda limit: rate_limit_exceeded('auth.resend_verification_email'))
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