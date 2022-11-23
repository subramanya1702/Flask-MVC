import json

from flask import current_app as app, request
from google.cloud import datastore

from auth.auth_helper import decode_auth_token, AuthError

client = datastore.Client()


def get_all_users():
    users_query = client.query(kind="users")
    all_users = list(users_query.fetch())
    user_response = []

    for user in all_users:
        user_response.append({
            "id": user.key.id,
            "sub": user["sub"]
        })

    response = app.make_response(json.dumps(user_response))
    response.mimetype = 'application/json'
    response.status_code = 200
    return response


def create_user(auth_token):
    payload = decode_auth_token(auth_token)
    user_id = payload["sub"]

    users_query = client.query(kind="users")
    users_query.add_filter("sub", "=", user_id)
    all_users = list(users_query.fetch())

    if len(all_users) == 0:
        new_user = datastore.Entity(key=client.key('users'))
        new_user.update({
            "sub": user_id
        })
        client.put(new_user)

    return user_id


def validate_accept_header():
    accept = request.headers.get('Accept')
    if accept != "application/json":
        raise AuthError({
            "Error": "Accept header {0} is not supported. Valid accept header is: application/json"
            .format(accept)
        }, 406)
