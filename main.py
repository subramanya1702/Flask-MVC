import json
from urllib.parse import urlencode, quote_plus

from authlib.integrations.flask_client import OAuth
from flask import Flask, request, jsonify, render_template, url_for, redirect
from google.cloud import datastore
from jose import jwt
from six.moves.urllib.request import urlopen

import constants

app = Flask(__name__)
client = datastore.Client()

oauth = OAuth(app)

oauth.register(
    "auth0",
    client_id=constants.CLIENT_ID,
    client_secret=constants.CLIENT_SECRET,
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f'https://{constants.DOMAIN}/.well-known/openid-configuration'
)


@app.route('/', methods=['GET'])
def pseudo_welcome():
    return render_template('welcome.html')


@app.route('/welcome', methods=['GET'])
def welcome():
    return render_template('welcome.html')


@app.route("/login")
def login():
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("callback", _external=True)
    )


@app.route("/callback", methods=["GET", "POST"])
def callback():
    token = oauth.auth0.authorize_access_token()
    return render_template('data.html', token=token["id_token"])


@app.route("/logout")
def logout():
    return redirect(
        "https://" + constants.DOMAIN
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": url_for("welcome", _external=True),
                "client_id": constants.CLIENT_ID,
            },
            quote_via=quote_plus,
        )
    )


@app.route('/boats', methods=['POST', 'GET'])
def get_all_and_create_boat():
    if request.method == 'POST':
        # Extract JWT and check its validity
        payload = verify_jwt(request)
        owner = payload["sub"]

        content = request.get_json()

        new_boat = datastore.Entity(key=client.key('boats'))
        new_boat.update({
            "name": content["name"],
            "type": content["type"],
            "length": content["length"],
            "public": content["public"],
            "owner": owner
        })
        client.put(new_boat)

        self = request.base_url + "/{0}".format(new_boat.key.id)

        response = {
            "id": new_boat.key.id,
            "name": new_boat["name"],
            "type": new_boat["type"],
            "length": new_boat["length"],
            "public": content["public"],
            "owner": owner,
            "self": self
        }
        return json.dumps(response), 201

    elif request.method == 'GET':
        try:
            # Extract JWT and check its validity
            payload = verify_jwt(request)
        except AuthError:
            payload = ""

        if payload is None or payload == "":
            boats_query = client.query(kind="boats")
            boats_query.add_filter("public", "=", True)
            all_boats = list(boats_query.fetch())
        else:
            owner = payload["sub"]
            boats_query = client.query(kind="boats")
            boats_query.add_filter("owner", "=", owner)
            all_boats = list(boats_query.fetch())

        for boat in all_boats:
            boat["id"] = boat.key.id
            boat["self"] = request.base_url

        return json.dumps(all_boats), 200


def verify_jwt(request):
    if 'Authorization' in request.headers:
        auth_header = request.headers['Authorization'].split()
        token = auth_header[1]
    else:
        raise AuthError({"code": "no auth header",
                         "description":
                             "Authorization header is missing"}, 401)

    jsonurl = urlopen("https://" + constants.DOMAIN + "/.well-known/jwks.json")
    jwks = json.loads(jsonurl.read())
    try:
        unverified_header = jwt.get_unverified_header(token)
    except jwt.JWTError:
        raise AuthError({"code": "invalid_header",
                         "description":
                             "Invalid header. "
                             "Use an RS256 signed JWT Access Token"}, 401)
    if unverified_header["alg"] == "HS256":
        raise AuthError({"code": "invalid_header",
                         "description":
                             "Invalid header. "
                             "Use an RS256 signed JWT Access Token"}, 401)
    rsa_key = {}
    for key in jwks["keys"]:
        if key["kid"] == unverified_header["kid"]:
            rsa_key = {
                "kty": key["kty"],
                "kid": key["kid"],
                "use": key["use"],
                "n": key["n"],
                "e": key["e"]
            }
    if rsa_key:
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=constants.ALGORITHMS,
                audience=constants.CLIENT_ID,
                issuer="https://" + constants.DOMAIN + "/"
            )
        except jwt.ExpiredSignatureError:
            raise AuthError({"code": "token_expired",
                             "description": "token is expired"}, 401)
        except jwt.JWTClaimsError:
            raise AuthError({"code": "invalid_claims",
                             "description":
                                 "incorrect claims,"
                                 " please check the audience and issuer"}, 401)
        except Exception:
            raise AuthError({"code": "invalid_header",
                             "description":
                                 "Unable to parse authentication"
                                 " token."}, 401)
        return payload
    else:
        raise AuthError({"code": "no_rsa_key",
                         "description":
                             "No RSA key in JWKS"}, 401)


class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


@app.errorhandler(AuthError)
def handle_auth_error(ex):
    response = jsonify(ex.error)
    response.status_code = ex.status_code
    return response


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
