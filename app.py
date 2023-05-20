import os
import random
from logging.handlers import RotatingFileHandler

import cherrypy
from flask import Flask, request, session, redirect, send_from_directory
from flask_babel import Babel
from flask_wtf.csrf import CSRFProtect
from paste.translogger import TransLogger

from config import webapp_settings
from controller import server, master


app = Flask(__name__)
app.register_blueprint(server.app, url_prefix='')
app.register_blueprint(master.app, url_prefix='')

# setting for babel
babel = Babel(app)


# removed this annotation as it seems no longer supported in Flask 2.3.2
# instead using babel.init_app.
#     - Adari
#@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(['ja', 'ja_JP', 'en', 'zh'])

babel.init_app(app, locale_selector=get_locale)

# setting for wtf
CSRFProtect(app)
app.config['WTF_CSRF_CHECK_DEFAULT'] = False


app.secret_key = webapp_settings['app_secret_key']


def create_app():
    return app


@app.before_request
def make_session_permanent():
    session.permanent = True


# プロトコルでhttpsが指定されているときは強制的にhttpsにリダイレクト
@app.before_request
def ssl_redirect():
    if webapp_settings['protocol'] == 'https://':
        if 'X-Forwarded-Proto' not in request.headers or request.headers['X-Forwarded-Proto'] != 'https':
            url = request.url.split('://')
            url[0] = 'https'
            url[1] = webapp_settings['domain'] + '/' + '/'.join(url[1].split('/')[1:])
            return redirect('://'.join(url), 301)


@app.route('/static/<path:path>', methods=['GET', 'POST'])
def send_static_cdn(path):
    return send_from_directory('static/', path)


if __name__ == '__main__':
    random.seed()
    log_dir = 'log/'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    handler = RotatingFileHandler(
        log_dir + 'webapp.log', maxBytes=10000000, backupCount=50)
    app.logger.addHandler(handler)
    app.logger.setLevel(webapp_settings['logging_level'])
    port = 5250
    # Flask on CherryPy
    app_logged = TransLogger(app)
    cherrypy.tree.graft(app_logged, '/')
    cherrypy.config.update({
        'engine.autoreload_on': True,
        'log.screen': True,
        'server.socket_port': port,
        'server.socket_host': '0.0.0.0'
    })
    cherrypy.engine.start()
    cherrypy.engine.block()
