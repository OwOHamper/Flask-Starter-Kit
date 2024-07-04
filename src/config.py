import logging
import os

from dotenv import load_dotenv

load_dotenv()


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



PRODUCTION = os.getenv('PRODUCTION')
HOST = os.getenv('HOST')
PORT = os.getenv('PORT')
MONGO_URI = os.getenv('MONGO_URI')

if None in (PORT, MONGO_URI):
    raise ValueError('One or more environmental variables are missing!')

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