from flask import request, session, g
from src.config import ACCEPTED_LANGUAGES
from flask_login import current_user


def update_user_locale(locale):
    if current_user.is_authenticated:
        g.lang = locale
        g.set_user_locale = True

def get_locale():
    lang = request.args.get('lang')
    
    g.set_lang_cookie = False
    g.set_user_locale = False
    
    if lang in ACCEPTED_LANGUAGES:
        g.lang = lang
        g.set_lang_cookie = True
        update_user_locale(lang)
        return lang
    
    if 'lang' in request.cookies:
        if request.cookies['lang'] in ACCEPTED_LANGUAGES:
            update_user_locale(request.cookies['lang'])           
            return request.cookies['lang']
    return request.accept_languages.best_match(ACCEPTED_LANGUAGES)