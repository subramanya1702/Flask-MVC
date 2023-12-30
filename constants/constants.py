ALGORITHMS = ["RS256"]
DOMAIN = "xyz.auth.com"
CLIENT_ID = "client_id"
CLIENT_SECRET = "client_secret"
SECRET_KEY = "secret_key"

content_type_error = "Content-Type not supported. Application only supports type application/json"
missing_attributes_error = "The request object is missing at least one of the required attributes"
name_attribute_error = "The attribute 'name' is not valid"
model_attribute_error = "The attribute 'model' is not valid"
reg_num_attribute_error = "The attribute 'reg_num' is not valid"
color_attribute_error = "The attribute 'color' is not valid"
name_attribute_invalid_chars_error = "The attribute 'name' contains invalid characters"
attribute_length_error = "The attribute '{0}' cannot contain more than 100 characters"
attribute_max_length = 100
reg_num_max_length = 10
reg_num_max_length_error = "The attribute 'reg_num' cannot contain more than 10 characters"
car_with_name_exists_error = "A car with name {0} already exists"
invalid_attribute_error = "The attribute '{0}' is not valid"

car_not_found_error = "No car with this car_id exists"
spare_not_found_error = "No spare with this spare_id exists"
spare_installed_error = "The spare is already installed on another car"
car_not_installed_with_spare_error = "No car with this car_id is installed with the spare with this spare_id"

all_attributes_error = "Bad HTTP method. PATCH cannot update all attributes, please use PUT operation."
