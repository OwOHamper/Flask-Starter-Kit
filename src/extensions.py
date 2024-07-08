from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from flask_seasurf import SeaSurf
from flask_compress import Compress
from flask_minify import Minify
from flask_babel import Babel
from flask_login import LoginManager
from flask_talisman import Talisman
from flask_mail import Mail

from src import config
from src.localization import get_locale

from itsdangerous import URLSafeTimedSerializer

limiter = Limiter(
    get_remote_address,
    storage_uri=config.MONGO_URI,
    strategy='fixed-window', # 'moving-window' when you want to prevent burst attacks
)


mongo = PyMongo()
bcrypt = Bcrypt()
seasurf = SeaSurf()
mail = Mail()

babel = Babel()
talisman = Talisman()

login_manager = LoginManager()
login_manager.login_view = 'auth.login'


if config.PRODUCTION:
    compress = Compress()
    minify = Minify(html=True, js=True, cssless=True, go=False)



serializer = URLSafeTimedSerializer(config.SERIALIZER_SECRET_KEY)


def init_extensions(app):
    limiter.init_app(app)
    
    mongo.init_app(app)
    bcrypt.init_app(app)
    seasurf.init_app(app)
    mail.init_app(app)
    babel.init_app(app, locale_selector=get_locale)
    login_manager.init_app(app)
    
    #You can enable force_https if you have a SSL certificate and everything set up
    #Also depends on your proxy setup
    talisman.init_app(app, force_https=config.FORCE_HTTPS, content_security_policy=config.CSP)
    
    if config.PRODUCTION:
        compress.init_app(app)
        minify.init_app(app)