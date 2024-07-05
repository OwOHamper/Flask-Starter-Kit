from flask import Blueprint, render_template, request, send_from_directory
from src.localization import get_locale

auth = Blueprint('auth', __name__)

@auth.route('/login')
def login():
    return render_template('pages/auth/login.html', locale=get_locale())

@auth.route('/register')
@auth.route('/signup')
def register():
    return render_template('pages/auth/register.html', locale=get_locale())

@auth.route('/logout')
def logout():
    return render_template('pages/auth/logout.html', locale=get_locale())