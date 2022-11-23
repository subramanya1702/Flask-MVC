import json

from flask import request, current_app as app
from google.cloud import datastore

from auth.auth_helper import verify_jwt, AuthError
from constants import constants

client = datastore.Client()


def get_all_and_create_car():
    if request.method == 'POST':
        validate_content_type()

        payload = verify_jwt(request)
        user_id = payload["sub"]
        content = request.get_json()

        # Validate request body
        validate_car_request_body(content)

        # No need to filter using user id.
        # Car name should be unique across all users
        cars_query = client.query(kind="cars")
        cars_query.add_filter("name", "=", content["name"])
        all_cars = list(cars_query.fetch())

        # Check if a car with the name already exists in datastore
        if len(all_cars) > 0:
            return {"Error": constants.car_with_name_exists_error.format(content["name"])}, 403

        # Add car to datastore
        new_car = datastore.Entity(key=client.key('cars'))
        new_car.update({
            "name": content["name"],
            "model": content["model"],
            "reg_num": content["reg_num"],
            "color": content["color"],
            "user_id": user_id
        })
        client.put(new_car)

        self = request.base_url + "/{0}".format(new_car.key.id)

        response = {
            "id": new_car.key.id,
            "name": new_car["name"],
            "model": new_car["model"],
            "reg_num": new_car["reg_num"],
            "color": new_car["color"],
            "self": self
        }

        response = app.make_response(json.dumps(response))
        response.mimetype = 'application/json'
        response.status_code = 201
        return response

    elif request.method == 'GET':
        validate_accept_header()

        payload = verify_jwt(request)
        user_id = payload["sub"]

        cars_query = client.query(kind="cars")
        cars_query.add_filter("user_id", "=", user_id)
        limit = int(request.args.get('limit', '5'))
        offset = int(request.args.get('offset', '0'))
        left_iterator = cars_query.fetch(limit=limit, offset=offset)
        pages = left_iterator.pages
        all_cars = list(next(pages))

        # If there are no cars created by the user, return an empty list
        if len(all_cars) == 0:
            return {"cars": []}, 200

        if left_iterator.next_page_token:
            next_offset = offset + limit
            next_url = request.base_url + "?limit=" + str(limit) + "&offset=" + str(next_offset)
        else:
            next_url = None

        for car in all_cars:
            car["id"] = car.key.id
            car["self"] = request.base_url + "/" + str(car.key.id)
            car["spares"] = get_spares_for_car(car.key.id)

        output = {"cars": all_cars}

        if next_url:
            output["next"] = next_url

        response = app.make_response(json.dumps(output))
        response.mimetype = 'application/json'
        response.status_code = 200
        return response
    else:
        return {"Error": "Method not supported!"}, 405


def get_update_and_delete_car(car_id):
    car_id = int(car_id)

    if request.method == 'GET':
        validate_accept_header()

        car = perform_basic_validations(car_id)

        # Get spares that are installed in the car
        installed_spares = get_spares_for_car(car_id)

        car["id"] = car_id
        car["spares"] = installed_spares
        car["self"] = request.base_url

        response = app.make_response(json.dumps(car))
        response.mimetype = 'application/json'
        response.status_code = 200
        return response

    elif request.method == 'PUT':
        validate_content_type()

        car = perform_basic_validations(car_id)

        content = request.get_json()
        validate_car_request_body(content)

        if car['name'] != content['name']:
            cars_query = client.query(kind="cars")
            cars_query.add_filter("name", "=", content["name"])
            all_cars = list(cars_query.fetch())

            # Check if a car with the name already exists in datastore
            if len(all_cars) > 0:
                return {"Error": constants.car_with_name_exists_error.format(content["name"])}, 403

        car.update(content)
        client.put(car)

        car["id"] = car_id
        car["self"] = request.base_url

        response = app.make_response(json.dumps(car))
        response.mimetype = 'application/json'
        response.status_code = 200
        return response

    elif request.method == 'PATCH':
        validate_content_type()

        car = perform_basic_validations(car_id)

        content = request.get_json()
        validate_car_request_body_for_patch(content)

        if "name" in content and car['name'] != content['name']:
            cars_query = client.query(kind="cars")
            cars_query.add_filter("name", "=", content["name"])
            all_cars = list(cars_query.fetch())

            # Check if a car with the name already exists in datastore
            if len(all_cars) > 0:
                return {"Error": constants.car_with_name_exists_error.format(content["name"])}, 403

        car.update(content)
        client.put(car)

        car["id"] = car_id
        car["self"] = request.base_url

        response = app.make_response(json.dumps(car))
        response.mimetype = 'application/json'
        response.status_code = 200
        return response

    elif request.method == 'DELETE':
        car = perform_basic_validations(car_id)

        # Get spares that are installed on the car
        spares_query = client.query(kind="spares")
        spares_query.add_filter("car_id", "=", car_id)
        all_spares = list(spares_query.fetch())

        # Remove the spares from the car
        if all_spares.__len__() > 0:
            for spare in all_spares:
                spare["car_id"] = None
                client.put(spare)

        # Delete car
        client.delete(car.key.id)
        return "", 204


def install_and_remove_spare(car_id, spare_id):
    car_id = int(car_id)
    spare_id = int(spare_id)

    if request.method == 'PUT':
        # Check if the car exists
        car_key = client.key('cars', int(car_id))
        car = client.get(key=car_key)
        if car is None:
            return {"Error": constants.car_not_found_error}, 404

        # Check if the spare exists
        spare_key = client.key('spares', int(spare_id))
        spare = client.get(key=spare_key)
        if spare is None:
            return {"Error": constants.spare_not_found_error}, 404

        # Check if the spare is already assigned to a car
        if "car_id" in spare and spare["car_id"] is not None:
            return {"Error": constants.spare_installed_error}, 403

        # Assign spare to the car
        spare["car_id"] = car_id
        client.put(spare)
        return "", 204

    elif request.method == 'DELETE':
        # Check if the car exists
        car_key = client.key('cars', int(car_id))
        car = client.get(key=car_key)
        if car is None:
            return {"Error": constants.car_not_found_error}, 404

        # Check if the spare exists
        spare_key = client.key('spares', int(spare_id))
        spare = client.get(key=spare_key)
        if spare is None:
            return {"Error": constants.spare_not_found_error}, 404

        # Check if the spare is installed on the car
        if "car_id" not in spare or spare["car_id"] is None or spare["car_id"] != car_id:
            return {"Error": constants.car_not_installed_with_spare_error}, 404

        spare["car_id"] = None
        client.put(spare)
        return "", 204


def get_spares_for_car(car_id):
    # Get spares that are installed on the car
    spares_query = client.query(kind="spares")
    spares_query.add_filter("car_id", "=", car_id)
    all_spares = list(spares_query.fetch())
    installed_spares = []

    for spare in all_spares:
        self = request.host_url + "spares/{0}".format(spare.key.id)
        installed_spares.append({
            "id": spare.key.id,
            "self": self
        })
    return installed_spares


def perform_basic_validations(car_id):
    payload = verify_jwt(request)
    user_id = payload["sub"]

    car_key = client.key('cars', int(car_id))
    car = client.get(key=car_key)
    if car is None:
        return {"Error": constants.car_not_found_error}, 404

    if car["user_id"] != user_id:
        return {"Error": "Invalid user. The car_id belongs to a different user"}, 400

    return car


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


def validate_car_request_body(content):
    # Check if all attributes are present
    if ("name" not in content) or ("model" not in content) or ("reg_num" not in content) \
            or ("color" not in content):
        raise AuthError({"Error": constants.missing_attributes_error}, 400)

    validate_name(content)
    validate_model(content)
    validate_reg_num(content)
    validate_color(content)


def validate_car_request_body_for_patch(content):
    # Check if id is present in the request body
    if "id" in content:
        return {"Error": "Attribute 'Id' cannot be updated."}

    # Check if all attributes are not present
    if {"name", "model", "reg_num", "color"} <= content.keys():
        raise AuthError({"Error": constants.all_attributes_error}, 400)

    validate_name(content)
    validate_model(content)
    validate_reg_num(content)
    validate_color(content)


def validate_name(content):
    # Check if the name attribute is a string
    if "name" in content and not isinstance(content["name"], str):
        raise AuthError({"Error": constants.name_attribute_error}, 400)

    # Check if the name attribute has more than 100 characters
    if "name" in content and len(content["name"]) > constants.attribute_max_length:
        raise AuthError({"Error": constants.attribute_length_error.format("name")}, 400)


def validate_model(content):
    # Check if the type attribute is a string
    if "model" in content and not isinstance(content["model"], str):
        raise AuthError({"Error": constants.model_attribute_error}, 400)

    # Check if the model attribute has more than 100 characters
    if "model" in content and len(content["model"]) > constants.attribute_max_length:
        raise AuthError({"Error": constants.attribute_length_error.format("model")}, 400)


def validate_reg_num(content):
    # Check if the reg_num attribute is a string
    if "reg_num" in content and not isinstance(content["reg_num"], str):
        raise AuthError({"Error": constants.reg_num_attribute_error}, 400)

    # Check if the reg_num attribute has more than 10 characters
    if "reg_num" in content and len(content["reg_num"]) > constants.reg_num_max_length:
        raise AuthError({"Error": constants.reg_num_max_length_error}, 400)


def validate_color(content):
    # Check if the color attribute is a string
    if "color" in content and not isinstance(content["color"], str):
        raise AuthError({"Error": constants.color_attribute_error}, 400)

    # Check if the color attribute has more than 100 characters
    if "color" in content and len(content["color"]) > constants.attribute_max_length:
        raise AuthError({"Error": constants.attribute_length_error.format("color")}, 400)
