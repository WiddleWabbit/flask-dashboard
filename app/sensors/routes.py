from flask import Blueprint, Flask, request, render_template, url_for, redirect, flash
from flask_login import current_user
from app.sensors.models import Sensors, WaterDepth, db
from app.sensors.func import calculate_calibration_value, get_all_sensors, update_sensor, delete_sensor
from app.func import sanitise, update_status_messages, flash_status_messages, delete_status_messages, count_fields

bp = Blueprint('sensors_routes', __name__)

# Return the variables to build the sensors page
def config_sensors():
    data = {}
    data['sensors'] = get_all_sensors()
    if not data['sensors']:
        data['sensors'] = [{"id":1, "name":"", "identifier":"", "calibration":"", "type":"", "sort_order":"", "calibration_mode": ""}]
    return data

# Sensors Route
@bp.route("/sensors", methods=["GET", "POST"])
def sensors():

    if request.method == "GET":
        
        return render_template('sensors.html', data=config_sensors())
    
    if request.method == "POST":

        if request.args.get("form") == "update_sensors":

            # Check authenticated
            if not current_user.is_authenticated:
                flash('You need to login to make modifications.', 'danger')
                return render_template('sensors.html', data=config_sensors()), 403
            
            # Fetch the fields and process
            fields = request.form.items()
            if fields:

                # Process the fields
                num_sensors = count_fields(fields)
                all_sensors = get_all_sensors()
                update_results = {}
                delete_results = {}

                # Update submitted sesnors
                for i in range(1, num_sensors + 1):

                    # Collect form inputs
                    if request.form.get(f'id-{i}') == "" or request.form.get(f'id-{i}') == "None":
                        id = None
                    else:
                        id = sanitise(request.form.get(f"id-{i}"), int)

                    if request.form.get(f'calibration-{i}') == "" or request.form.get(f'calibration-{i}') == "None":
                        calibration = 0
                    else:
                        calibration = sanitise(request.form.get(f"calibration-{i}"), int)

                    name = sanitise(request.form.get(f"name-{i}"))
                    type = sanitise(request.form.get(f"type-{i}"))
                    identifier = sanitise(request.form.get(f"identifier-{i}"))
                    calibration = sanitise(request.form.get(f"calibration-{i}"), float)
                    calibration_mode = sanitise(request.form.get(f"calibration-mode-{i}"), str)
                    sort_order = sanitise(request.form.get(f"sort-order-{i}"), int)

                    # If the non required fields are blank, set them to default values
                    if not calibration:
                        calibration = 0.00
                    if not name:
                        name = ""
                    # Set calibration mode
                    if calibration_mode == "on":
                        calibration_mode = 1
                    else:
                        calibration_mode = 0

                    # Validate form fields
                    if not id == None:
                        if not isinstance(id, int) or id < 0: # REPLICATE IN SCHEDULES LOGIC?
                            print(f'ID submitted not valid {id}')
                            update_results[f'Sensor {id} "{name}"'] = False
                            continue
                    if not isinstance(name, str):
                        print(f'Name not valid {name}')
                        update_results[f'sensor-{i}'] = False
                        continue
                    if not type in {'waterdepth', 'temperature'}:
                        print(f'Type not valid {type}')
                        update_results[f'sensor-{i}'] = False
                        continue
                    if identifier == None:
                        print(f'Identifier not valid {identifier}')
                        update_results[f'sensor-{i}'] = False
                        continue
                    # Ensure Identifiers are unique
                    existing_identifier = Sensors.query.filter_by(identifier=identifier).first()
                    if existing_identifier:
                        if existing_identifier.id != id:
                            print(f'Cannot use duplicate identifier: {identifier}')
                            flash('All identifiers must be unique.', 'warning')
                            update_results[f'sensor-{i}'] = False
                            continue
                    if calibration is False or not isinstance(calibration, float):
                        print(f'Calibration not valid {calibration}')
                        update_results[f'sensor-{i}'] = False
                        continue
                    if not isinstance(calibration_mode, int) or calibration_mode > 1 or calibration_mode < 0:
                        print(f'Calibration mode not valid {calibration_mode}')
                        update_results[f'sensor-{i}'] = False
                        continue
                    if not isinstance(sort_order, int) or sort_order < 0:
                        print(f'Sort Order not valid {sort_order}')
                        update_results[f'sensor-{i}'] = False
                        continue

                    # Has this sensor been brought out of calibration mode, if so create the new calibration offset
                    if not calibration_mode:
                        sensor = Sensors.query.filter_by(id=id).first()
                        if sensor and sensor.calibration_mode == 1:
                            calibration = calculate_calibration_value(identifier)

                    # Update the sensor
                    update_results[f'Sensor "{name}"'] = update_sensor(id, name, type, identifier, calibration, calibration_mode, sort_order)

                # Check for unsubmitted sensors and delete
                if all_sensors:
                    for sensor in all_sensors:
                        found = 0
                        for i in range(1, num_sensors + 1):
                            id = sanitise(request.form.get(f"id-{i}"), int)
                            if id == int(sensor.id):
                                found = 1
                                break
                        if found == 0:
                            delete_results[f'Sensor: {sensor.id}'] = delete_sensor(sensor.id)

                # Flash the messages of the updates and deletes
                update_messages = update_status_messages(update_results)
                flash_status_messages(update_messages)
                delete_messages = delete_status_messages(delete_results)
                flash_status_messages(delete_messages)
                return redirect(url_for("sensors_routes.sensors"))

            else:
                
                flash('Empty form submitted', 'danger')
                return redirect(url_for("sensors_routes.sensors"))