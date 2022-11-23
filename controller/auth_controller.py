from urllib.parse import urlencode, quote_plus

from authlib.integrations.flask_client import OAuth
from flask import render_template, url_for, redirect, current_app as app

from constants import constants
from service import user_service

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


def welcome():
    return render_template('welcome.html')


def login():
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("blueprint.callback", _external=True)
    )


def callback():
    token_payload = oauth.auth0.authorize_access_token()
    user_id = user_service.create_user(token_payload["id_token"])
    return render_template('data.html', token=token_payload["id_token"], userId=user_id)


def logout():
    return redirect(
        "https://" + constants.DOMAIN
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": url_for("blueprint.welcome", _external=True),
                "client_id": constants.CLIENT_ID,
            },
            quote_via=quote_plus,
        )
    )
