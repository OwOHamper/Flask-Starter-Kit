from datetime import datetime, timezone

import uuid

from urllib.parse import urlencode
import logging, secrets, requests
from json import JSONDecodeError


from flask import Blueprint, render_template, request, jsonify, url_for, redirect, abort, session, flash
from flask_login import login_user, logout_user, current_user
from flask_mail import Message

from src.extensions import limiter, mongo, serializer, mail
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
            'id': userinfo.get('sub'),
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
                    'id': userinfo.get('id'),
                    'email': email['email'],
                    'email_verified': email['verified'],
                    'picture': userinfo.get('avatar_url'),
                    'name': userinfo.get('name'),
                    'bio': userinfo.get('bio'),
                }
                
    return {}
    


@oauth_bp.route('/authorize/<provider>')
def oauth2_authorize(provider):
    if current_user.is_authenticated:
        return redirect('/you-are-authenticated-log-out-first')
    
    provider_data = config.OAUTH2_PROVIDERS.get(provider)
    if not provider_data:
        abort(404)
        
    oauth2_state = secrets.token_urlsafe(16)
    session['oauth2_state'] = oauth2_state
    qs = urlencode({
        'client_id': provider_data['client_id'],
        'redirect_uri': url_for('auth.oauth.oauth2_callback', provider=provider, _external=True),
        'response_type': 'code',
        'scope': ' '.join(provider_data['scopes']),
        'state': oauth2_state
    })
    
    return redirect(f"{provider_data['authorize_url']}?{qs}")


@oauth_bp.route('/callback/<provider>')
def oauth2_callback(provider):
    if current_user.is_authenticated:
        return redirect('/you-are-authenticated-log-out-first')
        
    provider_data = config.OAUTH2_PROVIDERS.get(provider)
    if not provider_data:
        abort(404)
        
    if "error" in request.args:
        for key, value in request.args.items():
            if key.startswith("error"):
                flash(f"Error: {value}", "error")
                logging.error(f"Error from {provider}: {value}")
        return redirect(url_for('auth.login'))
    
    if request.args.get('state') != session.get('oauth2_state'):
        abort(401)
        
    if "code" not in request.args:
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
        abort(401)
    
    try:
        json_response = response.json()
    except JSONDecodeError as e:
        logging.error(f"Error decoding JSON response from {provider}: {e}")
        abort(401)
        
    oauth2_token = json_response.get('access_token')
    if not oauth2_token:
        abort(401)
        
    user_data = get_oauth2_user_data(provider, oauth2_token)
    
       
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