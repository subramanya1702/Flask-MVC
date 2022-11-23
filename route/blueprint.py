from flask import Blueprint

from controller import car_controller, spare_controller
from controller.auth_controller import welcome, login, logout, callback
from controller.car_controller import get_all_and_create_car
from controller.spare_controller import get_all_and_create_spare
from controller.user_controller import get_all_users

blueprint = Blueprint('blueprint', __name__)


# Welcome and Auth APIs
@blueprint.route('/', methods=['GET'])
def initial_page():
    return welcome()


blueprint.route('/welcome', methods=['GET'])(welcome)
blueprint.route('/login', methods=['GET'])(login)
blueprint.route('/callback', methods=['GET', 'POST'])(callback)
blueprint.route('/logout', methods=['GET'])(logout)

# Car APIs
blueprint.route('/cars', methods=['GET', 'POST'])(get_all_and_create_car)


@blueprint.route('/cars/<car_id>', methods=['GET', 'PUT', 'PATCH', 'DELETE'])
def get_and_delete_car(car_id):
    return car_controller.get_update_and_delete_car(car_id)


@blueprint.route('/cars/<car_id>/spares/<spare_id>', methods=['PUT', 'DELETE'])
def install_and_remove_spare(car_id, spare_id):
    return car_controller.install_and_remove_spare(car_id, spare_id)


# Spare APIs
blueprint.route('/spares', methods=['GET', 'POST'])(get_all_and_create_spare)


@blueprint.route('/spares/<spare_id>', methods=['GET', 'PUT', 'PATCH', 'DELETE'])
def get_and_delete_spare(spare_id):
    return spare_controller.get_update_and_delete_spare(spare_id)


# User APIs
blueprint.route('/users', methods=['GET'])(get_all_users)
