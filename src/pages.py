from flask import Blueprint, render_template, request, send_from_directory
from src.localization import get_locale

pages = Blueprint('pages', __name__)

@pages.route('/robots.txt')
@pages.route('/sitemap.xml')
def static_from_root():
    return send_from_directory(pages.static_folder, request.path[1:])

@pages.route('/')
@pages.route('/home')
def home():
    return render_template('pages/home.html', locale=get_locale())

@pages.route('/about')
def about():
    return render_template('pages/about.html', locale=get_locale())

@pages.route('/documentation')
def documentation():
    return render_template('pages/documentation.html', locale=get_locale())

@pages.route('/contact')
def contact():
    return render_template('pages/contact.html', locale=get_locale())