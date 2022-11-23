import datetime
import json

from flask import request, current_app as app
from google.cloud import datastore

from auth.auth_helper import AuthError
from constants import constants

client = datastore.Client()


def get_all_and_create_spare():
    if request.method == 'POST':
        validate_content_type()

        content = request.get_json()

        # Validate request body
        validate_spare_request_body(content)

        # Add spare to datastore
        new_spare = datastore.Entity(key=client.key('spares'))
        new_spare.update({
            "name": content["name"],
            "price": content["price"],
            "manu_date": str(datetime.datetime.now()),
            "serial_num": content["serial_num"]
        })
        client.put(new_spare)

        self = request.base_url + "/{0}".format(new_spare.key.id)

        response = {
            "id": new_spare.key.id,
            "name": new_spare["name"],
            "price": new_spare["price"],
            "manu_date": new_spare["manu_date"],
            "serial_num": new_spare["serial_num"],
            "self": self
        }

        response = app.make_response(json.dumps(response))
        response.mimetype = 'application/json'
        response.status_code = 201
        return response

    elif request.method == 'GET':
        validate_accept_header()

        spares_query = client.query(kind="spares")
        limit = int(request.args.get('limit', '5'))
        offset = int(request.args.get('offset', '0'))
        left_iterator = spares_query.fetch(limit=limit, offset=offset)
        pages = left_iterator.pages
        all_spares = list(next(pages))

        # If there are no spares, return an empty list
        if len(all_spares) == 0:
            return {"spares": []}, 200

        if left_iterator.next_page_token:
            next_offset = offset + limit
            next_url = request.base_url + "?limit=" + str(limit) + "&offset=" + str(next_offset)
        else:
            next_url = None

        for spare in all_spares:
            spare["id"] = spare.key.id
            spare["self"] = request.base_url + "/" + str(spare.key.id)

        output = {"spares": all_spares}

        if next_url:
            output["next"] = next_url

        response = app.make_response(json.dumps(output))
        response.mimetype = 'application/json'
        response.status_code = 200
        return response

    else:
        return {"Error": "Method not supported!"}, 405


def get_update_and_delete_spare(spare_id):
    spare_id = int(spare_id)

    if request.method == 'GET':
        validate_accept_header()

        spare = validate_and_get_spare(spare_id)

        # Get car details
        installed_car = get_installed_car_for_spare(spare)

        spare["id"] = spare_id
        spare["installed_car"] = installed_car
        spare["self"] = request.base_url

        response = app.make_response(json.dumps(spare))
        response.mimetype = 'application/json'
        response.status_code = 200
        return response

    elif request.method == 'PUT':
        validate_content_type()

        spare = validate_and_get_spare(spare_id)

        content = request.get_json()
        validate_spare_request_body(content)

        spare.update(content)
        client.put(spare)

        spare["id"] = spare_id
        spare["self"] = request.base_url

        response = app.make_response(json.dumps(spare))
        response.mimetype = 'application/json'
        response.status_code = 200
        return response

    elif request.method == 'PATCH':
        validate_content_type()

        spare = validate_and_get_spare(spare_id)

        content = request.get_json()
        validate_spare_request_body_for_patch(content)

        spare.update(content)
        client.put(spare)

        spare["id"] = spare_id
        spare["self"] = request.base_url

        response = app.make_response(json.dumps(spare))
        response.mimetype = 'application/json'
        response.status_code = 200
        return response

    elif request.method == 'DELETE':
        # Get spare
        spare = validate_and_get_spare(spare_id)

        # Delete spare
        client.delete(spare)
        return "", 204


def get_installed_car_for_spare(spare):
    # Get car details
    installed_car = {}
    if "car_id" in spare and spare["car_id"] is not None:
        car_query = client.query(kind="cars")
        car_key = client.key("cars", spare["car_id"])
        car_query.key_filter(car_key, "=")
        installed_car = list(car_query.fetch())[0]

        if installed_car is not None:
            self = request.host_url + "cars/{0}".format(installed_car.key.id)
            installed_car = {
                "id": installed_car.key.id,
                "name": installed_car["name"],
                "model": installed_car["model"],
                "self": self
            }

    return installed_car


def validate_and_get_spare(spare_id):
    spare_key = client.key('spares', int(spare_id))
    spare = client.get(key=spare_key)
    if spare is None:
        return {"Error": constants.spare_not_found_error}, 404

    return spare


def validate_spare_request_body(content):
    # Check if all attributes are present
    if ("name" not in content) or ("price" not in content) or ("serial_num" not in content):
        raise AuthError({"Error": constants.missing_attributes_error}, 400)

    validate_name(content)
    validate_price(content)
    validate_serial_num(content)


def validate_spare_request_body_for_patch(content):
    # Check if all attributes are not present
    if {"name", "price", "serial_num"} <= content.keys():
        raise AuthError({"Error": constants.all_attributes_error}, 400)

    validate_name(content)
    validate_price(content)
    validate_serial_num(content)


def validate_content_type():
    # Check if the content type header has the supported type
    content_type = request.headers.get('Content-Type')
    if content_type != 'application/json':
        return {"Error": constants.content_type_error}, 415


def validate_accept_header():
    accept = request.headers.get('Accept')
    if accept != "application/json":
        return {
                   "Error": "Accept header {0} is not supported. Valid accept header is: application/json"
                   .format(accept)
               }, 406


def validate_name(content):
    # Check if the name attribute is a string
    if "name" in content and not isinstance(content["name"], str):
        raise AuthError({"Error": constants.name_attribute_error}, 400)

    # Check if the name attribute has more than 100 characters
    if "name" in content and len(content["name"]) > constants.attribute_max_length:
        raise AuthError({"Error": constants.attribute_length_error.format("name")}, 400)


def validate_price(content):
    # Check if the price attribute is a float
    if "price" in content and not isinstance(content["price"], float):
        raise AuthError({"Error": constants.invalid_attribute_error.format("price")}, 400)


def validate_serial_num(content):
    # Check if the serial_num attribute is a string
    if "serial_num" in content and not isinstance(content["serial_num"], int):
        raise AuthError({"Error": constants.invalid_attribute_error.format("serial_num")}, 400)
