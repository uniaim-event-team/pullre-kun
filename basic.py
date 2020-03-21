from functools import wraps
import hashlib
from time import sleep

from flask import make_response, request
from werkzeug.datastructures import Authorization

from config import webapp_settings

# TODO
user_password_dict = {
    webapp_settings['basic_user']: webapp_settings['basic_password']
}


def need_basic_auth(f):
    @wraps(f)
    def deco_func(*args, **kwargs):
        return basic_authorization() or f(*args, **kwargs)

    return deco_func


def basic_authorization():
    scheme = 'Basic'

    def get_auth():
        _auth = request.authorization

        if _auth is None and 'Authorization' in request.headers:
            # Flask/Werkzeug do not recognize any authentication types
            # other than Basic or Digest, so here we parse the header by
            # hand
            try:
                auth_type, token = request.headers['Authorization'].split(None, 1)
                _auth = Authorization(auth_type, {'token': token})
            except ValueError:
                # The Authorization header is either empty or has no token
                pass

        # if the auth type does not match, we act as if there is no auth
        # this is better than failing directly, as it allows the callback
        # to handle special cases, like supporting multiple auth types
        if _auth is not None and _auth.type.lower() != scheme.lower():
            _auth = None

        return _auth

    auth = get_auth()

    # Flask normally handles OPTIONS requests on its own, but in the
    # case it is configured to forward those to the application, we
    # need to ignore authentication headers and let the request through
    # to avoid unwanted interactions with CORS.
    if request.method != 'OPTIONS':  # pragma: no cover
        if not auth or not auth.password or \
                hashlib.sha512(auth.password.encode()).hexdigest() != user_password_dict.get(auth.username):
            # defence for brute force
            sleep(1)
            realm = 'Authentication Required'
            res = make_response(realm)
            res.status_code = 401
            if 'WWW-Authenticate' not in res.headers.keys():
                res.headers['WWW-Authenticate'] = '{0} realm="{1}"'.format(scheme, realm)
            return res

    return None
