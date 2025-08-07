from flask import Blueprint, Flask, request, render_template, url_for, redirect, flash
from flask_login import current_user
from app.sensors.models import Sensors, WaterDepth, db
from app.sensors.func import *
from app.func import sanitise, update_status_messages, flash_status_messages, delete_status_messages, count_fields

bp = Blueprint('sensors_routes', __name__)

# Return the variables to build the sensors page
def config_sensors():
    data = {}
    data['sensors'] = get_all_sensors()
    if not data['sensors']:
        data['sensors'] = [{"id":1, "name":"", "identifier":"", "calibration":"", "type":"", "sort_order":""}]
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
                    sort_order = sanitise(request.form.get(f"sort-order-{i}"), int)

                    # If the non required fields are blank, set them to default values
                    if not calibration:
                        calibration = 0.00
                    if not name:
                        name = ""

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
                    if not type in {'waterdepth', 'temperature'}: # NEEDS TO BE REPLACED WITH MODEL SO NO DUPLICATION
                        print(f'Type not valid {type}')
                        update_results[f'sensor-{i}'] = False
                        continue
                    if identifier == None:
                        print(f'Identifier not valid {identifier}')
                        update_results[f'sensor-{i}'] = False
                        continue
                    if calibration is False or not isinstance(calibration, float):
                        print(f'Calibration not valid {calibration}')
                        update_results[f'sensor-{i}'] = False
                        continue
                    if not isinstance(sort_order, int) or sort_order < 0:
                        print(f'Sort Order not valid {sort_order}')
                        update_results[f'sensor-{i}'] = False
                        continue # FIX THIS ON SCHEDULES?

                    # Update the sensor
                    update_results[f'Sensor {id} "{name}"'] = update_sensor(id, name, type, identifier, calibration, sort_order)

                # Check for unsubmitted sensors and delete
                if all_sensors:
                    for sensor in all_sensors:
                        found = 0
                        print(f"Looking for sensor {sensor.id}")
                        for i in range(1, num_sensors + 1):
                            id = sanitise(request.form.get(f"id-{i}"), int)
                            print(f"Checking sensor {id}")
                            if id == int(sensor.id):
                                print(f"Found sensor {id}")
                                found = 1
                                break
                        if found == 0:
                            print(f"Deleting sensor {sensor.id}")
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