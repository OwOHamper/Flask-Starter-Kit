from flask import request, session
from src.config import ACCEPTED_LANGUAGES


def get_locale():
    if 'lang' in request.cookies:
        if request.cookies['lang'] in ACCEPTED_LANGUAGES:
            return request.cookies['lang']
    return request.accept_languages.best_match(ACCEPTED_LANGUAGES)