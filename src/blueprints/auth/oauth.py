import logging

from flask import Blueprint, render_template, request, jsonify, url_for
from flask_mail import Message

from src.extensions import limiter, mongo, serializer, mail
from src.utils import validate_email, rate_limit_exceeded
from src.localization import get_locale
from src import config

oauth_bp = Blueprint('oauth', __name__)


@oauth_bp.route('/authorize/<provider>')
def oauth2_authorize(provider):
    return provider