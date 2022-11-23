from service import spare_service


def get_all_and_create_spare():
    return spare_service.get_all_and_create_spare()


def get_update_and_delete_spare(spare_id):
    return spare_service.get_update_and_delete_spare(spare_id)
