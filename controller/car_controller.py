from service import car_service


def get_all_and_create_car():
    return car_service.get_all_and_create_car()


def get_update_and_delete_car(car_id):
    return car_service.get_update_and_delete_car(car_id)


def install_and_remove_spare(car_id, spare_id):
    return car_service.install_and_remove_spare(car_id, spare_id)
