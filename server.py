from flask import Flask, render_template, send_from_directory, request
import logging

from werkzeug.middleware.proxy_fix import ProxyFix
from flask_compress import Compress
from flask_minify import Minify
from flask_talisman import Talisman

from flask_babel import Babel

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from src import config
from src.localization import get_locale

from src.pages import pages

app = Flask(__name__)


#You can enable force_https if you have a SSL certificate and everything set up
Talisman(app, content_security_policy=config.CSP)
app.wsgi_app = ProxyFix(app.wsgi_app)

limiter = Limiter(
    get_remote_address,
    app=app,
    storage_uri=config.MONGO_URI,
    strategy='fixed-window', # 'moving-window' when you want to prevent burst attacks
)

babel = Babel(app, locale_selector=get_locale)


if config.PRODUCTION:
    Compress(app)
    Minify(app=app, html=True, js=True, cssless=True, go=False)


app.register_blueprint(pages)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('pages/404.html')

if __name__ == '__main__':
    logging.info(f"\n🎉 Starting server on http://{config.HOST}:{config.PORT} 🎉")
    
    if config.PRODUCTION:
        logging.info("🚨 Running in PRODUCTION mode 🚨")
        
        from waitress import serve
        serve(app, host=config.HOST, port=config.PORT)
    
    else:
        logging.info("🚨 Running in DEVELOPMENT mode 🚨")
        app.run(host=config.HOST, port=config.PORT, debug=True)