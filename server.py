from flask import Flask, render_template, g
import logging

from werkzeug.middleware.proxy_fix import ProxyFix

from src import config


from src.blueprints.pages import pages
from src.blueprints.auth import auth, login_manager



from src.extensions import init_extensions

def create_app():
    app = Flask(__name__)
    app.config['MONGO_URI'] = config.MONGO_URI
    app.config['SECRET_KEY'] = config.SECRET_KEY
    app.config['REMEMBER_COOKIE_DURATION'] = config.REMEMBER_COOKIE_DURATION
    app.config['PERMANENT_SESSION_LIFETIME'] = config.PERMANENT_SESSION_LIFETIME


    
    app.wsgi_app = ProxyFix(app.wsgi_app)

    init_extensions(app)


    

    app.register_blueprint(pages)
    app.register_blueprint(auth)


    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('pages/404.html')

    @app.after_request
    def set_lang_cookie(response):
        if g.get('set_cookie', False):
            response.set_cookie('lang', g.lang, max_age=60*60*24*365)
        return response

    return app


if __name__ == '__main__':
    app = create_app()
    
    logging.info(f"\n🎉 Starting server on http://{config.HOST}:{config.PORT} 🎉")

    if config.PRODUCTION:
        logging.info("🚨 Running in PRODUCTION mode 🚨")
        
        from waitress import serve
        serve(app, host=config.HOST, port=config.PORT)

    else:
        logging.info("🚨 Running in DEVELOPMENT mode 🚨")
        app.run(host=config.HOST, port=config.PORT, debug=True)