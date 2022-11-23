from flask import Flask

from constants import constants
from auth.auth_helper import handle_auth_error, AuthError
from route.blueprint import blueprint

app = Flask(__name__)
app.register_blueprint(blueprint, url_prefix="/")
app.register_error_handler(AuthError, handle_auth_error)
app.secret_key = constants.SECRET_KEY

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
