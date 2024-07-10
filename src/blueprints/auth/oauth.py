from datetime import datetime, timezone, timedelta

import uuid

from urllib.parse import urlencode
import logging, secrets, requests
from json import JSONDecodeError


from flask import Blueprint, render_template, request, jsonify, url_for, redirect, abort, session, flash, g
from flask_login import login_user, logout_user, current_user
from flask_mail import Message

from src.extensions import limiter, mongo, bcrypt
from src.localization import get_locale
from src import config

from src.blueprints.auth.auth_utils import validate_email, rate_limit_exceeded, build_user, User

oauth_bp = Blueprint('oauth', __name__)

def oauth2_endpoint_request(provider, endpoint, oauth2_token):
    provider_data = config.OAUTH2_PROVIDERS.get(provider)
    if not provider_data:
        abort(404)
    
    response = requests.get(provider_data['endpoints'][endpoint], headers={
        'Authorization': 'Bearer ' + oauth2_token,
        'Accept': 'application/json'
    })
    
    if response.status_code != 200:
        abort(401)
        
    try:
        json_response = response.json()
    except JSONDecodeError as e:
        logging.error(f"Error decoding JSON response from {provider}: {e}")
        abort(401)
        
    return json_response

def get_oauth2_user_data(provider, oauth2_token):
    if provider == 'google':
        userinfo = oauth2_endpoint_request(provider, 'userinfo', oauth2_token)
        return {
            'oauth_id': userinfo.get('sub'),
            'email': userinfo.get('email'),
            'email_verified': userinfo.get('email_verified'),
            'picture': userinfo.get('picture'),
            'name': userinfo.get('given_name'),
            'bio': None
        }
        
    elif provider == 'github':
        userinfo = oauth2_endpoint_request(provider, 'userinfo', oauth2_token)
        emailinfo = oauth2_endpoint_request(provider, 'emailinfo', oauth2_token)
                
        for email in emailinfo:
            if email['primary']:
                return {
                    'oauth_id': userinfo.get('id'),
                    'email': email['email'],
                    'email_verified': email['verified'],
                    'picture': userinfo.get('avatar_url'),
                    'name': userinfo.get('name'),
                    'bio': userinfo.get('bio'),
                }
                
    return {}
    


@oauth_bp.route('/authorize/<provider>')
def oauth2_authorize(provider):
    link = request.args.get('link')
    if current_user.is_authenticated:
        return redirect('/you-are-authenticated-log-out-first')
    
    provider_data = config.OAUTH2_PROVIDERS.get(provider)
    if not provider_data:
        abort(404)
        
    if link:
        redirect_url = url_for('auth.oauth.oauth2_callback_link', provider=provider, _external=True)
    else:
        redirect_url = url_for('auth.oauth.oauth2_callback', provider=provider, _external=True)
        
    oauth2_state = secrets.token_urlsafe(16)
    session['oauth2_state'] = oauth2_state
    qs = urlencode({
        'client_id': provider_data['client_id'],
        'redirect_uri': redirect_url,
        'response_type': 'code',
        'scope': ' '.join(provider_data['scopes']),
        'state': oauth2_state
    })
    
    return redirect(f"{provider_data['authorize_url']}?{qs}")



def callback_initialization(provider):
    if current_user.is_authenticated:
        return redirect('/you-are-authenticated-log-out-first')
        
    provider_data = config.OAUTH2_PROVIDERS.get(provider)
    if not provider_data:
        logging.debug(f"Provider not found: {provider}")
        abort(404)
        
    if "error" in request.args:
        for key, value in request.args.items():
            if key.startswith("error"):
                flash(f"Error: {value}", "error")
                logging.error(f"Error from {provider}: {value}")
        return redirect(url_for('auth.login'))
    
    if request.args.get('state') != session.get('oauth2_state'):
        logging.error(f"OAuth 2.0 state mismatch for {provider}")
        abort(401)
        
    if "code" not in request.args:
        logging.error(f"OAuth 2.0 code not provided for {provider}")
        abort(401)
        
    # exchange the authorization code for an access token
    response = requests.post(provider_data['token_url'], data={
        'client_id': provider_data['client_id'],
        'client_secret': provider_data['client_secret'],
        'code': request.args['code'],
        'grant_type': 'authorization_code',
        'redirect_uri': url_for('auth.oauth.oauth2_callback', provider=provider,
        _external=True
    )}, headers={'Accept': 'application/json'})
    
    if response.status_code != 200:
        logging.error(f"Error exchanging authorization code for access token from {provider}: {response.status_code} {response.text}")
        abort(401)
    
    try:
        json_response = response.json()
    except JSONDecodeError as e:
        logging.error(f"Error decoding JSON response from {provider}: {e}")
        abort(401)
        
    oauth2_token = json_response.get('access_token')
    if not oauth2_token:
        logging.debug(f"Access token not provided by {provider}")
        abort(401)
        
        
    user_data = get_oauth2_user_data(provider, oauth2_token)
    
    return {
        'oauth2_token': oauth2_token,
        'user_data': user_data,
    }
@oauth_bp.route('/callback/<provider>')
def oauth2_callback(provider):
    
    return_data = callback_initialization(provider)
    
    user_data = return_data['user_data']
    oauth2_token = return_data['oauth2_token']
       
    # FOR REFERENCE
    # {
    #     'email': email['email'],
    #     'email_verified': email['verified'],
    #     'picture': userinfo.get('avatar_url'),
    #     'name': userinfo.get('name'),
    #     'bio': userinfo.get('bio'),
    # }
    
    if not user_data.get('email'):
        flash("Email not provided by OAuth 2.0 provider", "error")
        return redirect(url_for('auth.login'))

    if user_data.get('email_verified') != True:
        flash("Email not verified by OAuth 2.0 provider", "error")
        return redirect(url_for('auth.login'))
    
    
    user = mongo.db.users.find_one({'email': user_data.get('email')})
    
    if not user:
        logging.info(f"Creating user from OAuth 2.0 provider: {provider}, email: {user_data.get('email')}")
        alternative_id = str(uuid.uuid4())
        
        user_model = build_user({
            'oauth_login': True,            
            'email': user_data.get('email'),
            'alternative_id': alternative_id,
            'auth_provider': provider,
            'profile_picture': user_data.get('picture'),
            'display_name': user_data.get('name'),
            'bio': user_data.get('bio'),
            
            'connections': {
                provider: {
                    'oauth_id': user_data.get('oauth_id'),
                    'token': oauth2_token,
                    'connected_at': datetime.now(tz=timezone.utc),
                    'last_updated': datetime.now(tz=timezone.utc),
                }
            }
        })
        
        user_id = mongo.db.users.insert_one(user_model).inserted_id
    
        userObject = User(alternative_id)
        
        session.clear()
        session.permanent = True
        
        login_user(userObject, remember=True)
        
        return redirect(url_for('pages.home'))
    else:
        if user['account_status'] != 'active':
            if user['account_status'] == 'deactivated':
                flash("Your account has been deactivated. Please contact support for assistance.", "error")
            elif user['account_status'] == 'suspended':
                flash("Your account has been suspended. Please contact support for assistance.", "error")
            else:
                flash("Your account is currently inactive. Please contact support for assistance.", "error")
            return redirect(url_for('auth.login'))
        elif not user['email_verified']:
            flash("Please verify your email address to activate your account. Check your inbox for a verification email or request a new one.", "error")
            return redirect(url_for('auth.login'))
        
        #User exists and provider is already connected to account
        if provider in user.get('connections', {}):
            
            updated_fields = {}
            if provider == user.get('auth_provider'):
                updated_fields = {
                    'profile.profile_picture': user_data.get('picture'),
                    'profile.display_name': user_data.get('name'),
                    'profile.bio': user_data.get('bio'),
                }
            
            
            mongo.db.users.update_one(
                {'_id': user['_id']},
                {
                    '$set': {
                        'last_login': datetime.now(tz=timezone.utc),
                        f'connections.{provider}.token': oauth2_token,
                        f'connections.{provider}.last_updated': datetime.now(tz=timezone.utc),
                        'metadata.last_login_ip': request.remote_addr,
                        'metadata.last_login_user_agent': request.headers.get('User-Agent'),
                        'security.failed_login_attempts': 0,
                    } | updated_fields,
                    '$inc': {
                        'usage_stats.total_logins': 1
                    }
                }
            )
            
            alternative_id = user['alternative_id']
            
            userObject = User(alternative_id)
        
            session.clear()
            session.permanent = True
            
            g.set_lang_cookie = True
            g.lang = user['preferences']['language']
            
            login_user(userObject, remember=True)
            
            return redirect(url_for('pages.home'))
        # Need to connect provider to account
        else:
            auth_provider = user.get('auth_provider')
            
            session['pending_oauth_connection'] = {
                'provider': provider,
                'auth_provider': auth_provider,
                'oauth_id': user_data.get('oauth_id'),
                'token': oauth2_token,
                'email': user_data.get('email'),
                'expires_at': datetime.now(tz=timezone.utc) + timedelta(hours=1)
            }
            return redirect(url_for('auth.oauth.link_account'))
            
         
@oauth_bp.route('/link/<provider>')
def oauth2_callback_link(provider):
    
    
    return_data = callback_initialization(provider)
    
    user_data = return_data['user_data']
    oauth2_token = return_data['oauth2_token']
    #TODO future, update this token to original provider also update profile data etc. it is updated on normal callback function but not here
    
    #FOR REFERENCE
    # session['pending_oauth_connection'] = {
    #     'provider': provider,
    #     'auth_provider': auth_provider,
    #     'oauth_id': user_data.get('oauth_id'),
    #     'token': oauth2_token,
    #     'email': user_data.get('email'),
    #     'expires_at': datetime.now(tz=timezone.utc) + timedelta(hours=1)
    # }
    
    
    if 'pending_oauth_connection' in session:
        logging.debug("Linking request")
        if session['pending_oauth_connection']['email'] != user_data.get('email') or \
        session['pending_oauth_connection']['auth_provider'] != provider or \
        session['pending_oauth_connection']['expires_at'] < datetime.now(tz=timezone.utc):
            logging.debug("Linking request failed")
            session.pop('pending_oauth_connection')
            session['linked_account'] = False
            return redirect(url_for('auth.oauth.linking_status'))
            
        logging.debug("Linking request succeeded")
        user = mongo.db.users.find_one({'email': user_data.get('email')})
        
        mongo.db.users.update_one(
            {'_id': user['_id']},
            {'$set': {
                    f'connections.{session["pending_oauth_connection"]["provider"]}': {
                        'oauth_id': session['pending_oauth_connection']['oauth_id'],
                        'token': session['pending_oauth_connection']['token'],
                        'connected_at': datetime.now(tz=timezone.utc),
                        'last_updated': datetime.now(tz=timezone.utc),
                    },
                    'last_login': datetime.now(tz=timezone.utc),
                    'metadata.last_login_ip': request.remote_addr,
                    'metadata.last_login_user_agent': request.headers.get('User-Agent'),
                    'security.failed_login_attempts': 0
                },
                '$inc': {
                    'usage_stats.total_logins': 1
                }
            }
        )
        
        userObject = User(user['alternative_id'])
            
        session.clear()
        session.permanent = True
            
        g.set_lang_cookie = True
        g.lang = user['preferences']['language']
            
        login_user(userObject, remember=True)
            
        session['linked_account'] = True
        
        return redirect(url_for('auth.oauth.linking_status'))
            
@oauth_bp.route('/link-account')
def link_account():
    if 'pending_oauth_connection' not in session:
        return redirect(url_for('auth.login'))
    
    if datetime.now(tz=timezone.utc) > session['pending_oauth_connection']['expires_at']:
        session.pop('pending_oauth_connection')
        return redirect(url_for('auth.login'))
    
    if session['pending_oauth_connection']['auth_provider'] == 'local':
        auth_method = "password"
    else:
        auth_method = "oauth"
    
    print(session['pending_oauth_connection'])
    
    return render_template('pages/auth/link-account.html', locale=get_locale(),
        email=session['pending_oauth_connection']['email'],
        auth_method=auth_method,
        existing_provider=session['pending_oauth_connection']['auth_provider'],
        new_provider=session['pending_oauth_connection']['provider']
    )
    
#This handles linking with auth_method=password
@oauth_bp.route('/link-account', methods=['POST'])
def link_account_post():
    email = request.json.get('email')
    password = request.json.get('password')
    
    if datetime.now(tz=timezone.utc) > session['pending_oauth_connection']['expires_at']:
        session.pop('pending_oauth_connection')
        return jsonify({'success': False, 'message': 'Linking session expired. Please try again.'}), 400
    
    user = mongo.db.users.find_one({'email': email})
        
    if user:
        if bcrypt.check_password_hash(user['password'], password):
            mongo.db.users.update_one(
                {'_id': user['_id']},
                {'$set': {
                        f'connections.{session["pending_oauth_connection"]["provider"]}': {
                            'oauth_id': session['pending_oauth_connection']['oauth_id'],
                            'token': session['pending_oauth_connection']['token'],
                            'connected_at': datetime.now(tz=timezone.utc),
                            'last_updated': datetime.now(tz=timezone.utc),
                        },
                        'last_login': datetime.now(tz=timezone.utc),
                        'metadata.last_login_ip': request.remote_addr,
                        'metadata.last_login_user_agent': request.headers.get('User-Agent'),
                        'security.failed_login_attempts': 0
                    },
                    '$inc': {
                        'usage_stats.total_logins': 1
                    }
                }
            )
            
            
            userObject = User(user['alternative_id'])
            
            session.clear()
            session.permanent = True
            
            g.set_lang_cookie = True
            g.lang = user['preferences']['language']
            
            login_user(userObject, remember=True)
            
            session['linked_account'] = True
            
            return jsonify({'success': True, 'message': 'Account linked successfully!'}), 200
            
            
        
    return jsonify({'success': False, 'message': 'Incorrect email or password.'}), 404

@oauth_bp.route('/linking-status')
def linking_status():
    if 'linked_account' not in session:
        return redirect(url_for('auth.login'))
    
    linked_status = session['linked_account']
    session.pop('linked_account')
    
    return render_template('pages/auth/link-status.html', locale=get_locale(), success=linked_status)