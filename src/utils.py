class ProxyFix:
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        
        if 'HTTP_X_FORWARDED_SCHEME' in environ:
            environ['wsgi.url_scheme'] = environ['HTTP_X_FORWARDED_SCHEME']

        if 'HTTP_X_REAL_IP' in environ:
            environ['REMOTE_ADDR'] = environ['HTTP_X_REAL_IP']

        return self.app(environ, start_response)