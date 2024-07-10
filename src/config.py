import logging, os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


WAITRESS_THREADS = 8


#CONSTANTS DEFINED HERE (config.py)
ACCEPTED_LANGUAGES = ['en', 'de', 'it', 'zh']
# See https://github.com/GoogleCloudPlatform/flask-talisman?tab=readme-ov-file#content-security-policy
CSP = {
    "default-src": "'self'",
    "script-src": [
        "'self'",
        "analytics.hamper.dev"
    ],
    "connect-src": [
        "'self'",
        "https://analytics.hamper.dev"
    ],
    "img-src": [
        "'self'",
        "data:"
    ],
}
REMEMBER_COOKIE_DURATION = timedelta(days=30)
PERMANENT_SESSION_LIFETIME = timedelta(days=30)

FORCE_HTTPS = False


MAIL_DEFAULT_SENDER = ("Hamper from Flask Starter Kit", "verification@flaskstarter.com")


#OAUTH 2.0 PROVIDERS CONFIG
OAUTH2_PROVIDERS = {
    # Google OAuth 2.0 documentation:
    # https://developers.google.com/identity/protocols/oauth2/web-server#httprest
    'google': {
        'client_id': os.environ.get('GOOGLE_CLIENT_ID'),
        'client_secret': os.environ.get('GOOGLE_CLIENT_SECRET'),
        'authorize_url': 'https://accounts.google.com/o/oauth2/auth',
        'token_url': 'https://accounts.google.com/o/oauth2/token',
        'userinfo': {
            'url': 'https://www.googleapis.com/oauth2/v3/userinfo',
            'email': lambda json: json['email'],
        },
        'scopes': ['https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile'],
    },

    # GitHub OAuth 2.0 documentation:
    # https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps
    'github': {
        'client_id': os.environ.get('GITHUB_CLIENT_ID'),
        'client_secret': os.environ.get('GITHUB_CLIENT_SECRET'),
        'authorize_url': 'https://github.com/login/oauth/authorize',
        'token_url': 'https://github.com/login/oauth/access_token',
        'userinfo': {
            'url': 'https://api.github.com/user/emails',
            'email': lambda json: json[0]['email'],
        },
        'scopes': ['user:email', 'read:user'],
    },
}


#CONSTANTS FROM ENVIRONMENTAL VARIABLES
PRODUCTION = os.getenv('PRODUCTION')
HOST = os.getenv('HOST')
PORT = os.getenv('PORT')
MONGO_URI = os.getenv('MONGO_URI')
SECRET_KEY = os.getenv('SECRET_KEY')
SERIALIZER_SECRET_KEY = os.getenv('SERIALIZER_SECRET_KEY')


#EMAIL STUFF
MAIL_SERVER = os.getenv('MAIL_SERVER')
MAIL_USERNAME = os.getenv('MAIL_USERNAME')
MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')

if None in (PRODUCTION, PORT, MONGO_URI, SECRET_KEY, SERIALIZER_SECRET_KEY):
    raise ValueError('One or more environmental variables are missing!')

if None in (MAIL_SERVER, MAIL_USERNAME, MAIL_PASSWORD):
    raise ValueError('One or more email environmental variables are missing!')

if HOST is None:
    HOST = '0.0.0.0'
    
PRODUCTION = PRODUCTION.lower() == 'true'




logging.basicConfig(
    filename="app.log",
    level=logging.DEBUG if not PRODUCTION else logging.INFO,
    format="%(module)-10s:%(lineno)-4d | %(levelname)-8s: %(asctime)s | %(message)s",
    datefmt="%d/%m/%y %H:%M:%S"
)


# Make sure we log to the console as well
consoleHandler = logging.StreamHandler()
logging.getLogger().addHandler(consoleHandler)


#disable pymongo debug logging
logging.getLogger('pymongo').setLevel(logging.INFO)