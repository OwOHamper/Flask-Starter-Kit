from flask import request, session, g
from src.config import ACCEPTED_LANGUAGES


def get_locale():
    lang = request.args.get('lang')
    
    g.set_cookie = False
    
    if lang in ACCEPTED_LANGUAGES:
        g.lang = lang
        g.set_cookie = True
        return lang
    
    if 'lang' in request.cookies:
        if request.cookies['lang'] in ACCEPTED_LANGUAGES:
            return request.cookies['lang']
    return request.accept_languages.best_match(ACCEPTED_LANGUAGES)