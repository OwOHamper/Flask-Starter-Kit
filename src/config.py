import logging, os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


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
    filename="server.log",
    level=logging.DEBUG if not PRODUCTION else logging.INFO,
    format="%(module)-10s:%(lineno)-4d | %(levelname)-8s: %(asctime)s | %(message)s",
    datefmt="%d/%m/%y %H:%M:%S"
)


# Make sure we log to the console as well
consoleHandler = logging.StreamHandler()
logging.getLogger().addHandler(consoleHandler)


#disable pymongo debug logging
logging.getLogger('pymongo').setLevel(logging.INFO)