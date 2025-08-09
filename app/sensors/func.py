from app.sensors.models import Sensors, db, CalibrationModeData, WaterDepth, Temperature

def get_all_sensors():
    """
    Retrieve all sensors from the database.

    :return: A list of all sensor objects if any exist, otherwise None.
    """
    try:
        sensors = Sensors.query.all()
        return sensors if sensors else None
    except Exception as e:
        print(f"Unable to get all sensors from database: {e}")
    return None

def get_sensor(id):
    """
    Retrieve a sensor from the database by its ID.

    :param id: The ID of the sensor to retrieve.
    :return: The sensor object if found, otherwise None.
    """
    try:
        sensor = Sensors.query.filter_by(id=id).first()
        return sensor if sensor else False
    except Exception as e:
        print(f"Unable to get sensor from database: {e}")
        return False
    return False

def update_sensor(id,  name, type, identifier, calibration, calibration_mode, sort_order):
    """
    Create or update a sensor in the database.

    If a sensor with the given ID exists, its name, description, and solenoid are updated.
    If it does not exist, a new sensor is created with the provided values.

    :param id: The ID of the sensor, to create a new id, supply None.
    :param name: The name of the sensor as a string.
    :param type: The type of sensor as a string.
    :param identifier: The identifier to ID of the sensor to read from the MQTT Messages.
    :param calibration: The calibration of the sensor as a float.
    :param sort_order: The order to display on the page as an int.
    :return: True for success, False for failure.
    """
    if not id == None:
        if not isinstance(id, int) or id < 0:
            print('Invalid ID supplied')
            return False
    if not isinstance(name, str) or not isinstance(type, str) or not isinstance(identifier, str) or not isinstance(calibration, float)or not isinstance(calibration_mode, int):
        print('Instance Invalid')
        return False
    if sort_order < 0:
        print('Invalid id or sort_order supplied')
        return False
    try:

        # NOT UPDATING ????? NOTHING BUT REPORTS SUCCESS
        if id:
            sensor = Sensors.query.filter_by(id=id).first()
            if sensor:
                sensor.name = name
                sensor.type = type
                sensor.identifier = identifier
                sensor.calibration = calibration
                sensor.calibration_mode = calibration_mode
                sensor.sort_order = sort_order
            else:
                sensor = Sensors(id=id, name=name, type=type, identifier=identifier, calibration=calibration, calibration_mode=calibration_mode, sort_order=sort_order)
                db.session.add(sensor)
        else:
            sensor = Sensors(name=name, type=type, identifier=identifier, calibration=calibration, calibration_mode=calibration_mode, sort_order=sort_order)
            db.session.add(sensor)
        db.session.commit()
        return True
    except Exception as e:
        print(f"Unable to update sensor: {e}")
        return False
    return False

def delete_sensor(id):
    """
    Delete a sensor from the database by its ID.

    :param id: The ID of the sensor to delete.
    :return: True if the sensor was deleted successfully, False otherwise.
    """
    try:
        sensor = Sensors.query.filter_by(id=id).first()
        if sensor:
            db.session.delete(sensor)
            db.session.commit()
            return True
        else:
            return False
    except Exception as e:
        print(f"Unable to delete sensor: {id}, error: {e}")
    return False

def update_reading(sensor_identifier, timestamp, reading):
    """
    Add a new sensor reading or update an existing reading.

    :param sensor_identifier: The MQTT identifier of the sensor as a string.
    :param timestamp: The timestamp of the reading.
    :param reading: The sensors reading as a float.
    :return: True for success, fase for failure.
    """
    try:
        # Find the sensor
        sensor = Sensors.query.filter_by(identifier=sensor_identifier).first()
        if not sensor:
            print(f"Sensor with identifier {sensor_identifier} not found.")
            return False

        # Get the model to update
        if sensor.type == "waterdepth":
            model = WaterDepth
        elif sensor.type == "temperature":
            model = Temperature
        # Override the model to update if in calibration mode
        if sensor.calibration_mode:
            model == CalibrationModeData
        if not model:
            print(f"Unknown sensor type or mode for sensor {sensor_identifier}.")
            return False
        
        # Check if a reading with the same timestamp and sensor_id already exists
        existing_reading = model.query.filter_by(sensor_id=sensor.id, timestamp=timestamp).first()

        # Either update the existing reading at this timestamp for this sensor, or add a new one if it doesn't exist.
        if existing_reading:
            existing_reading.value = reading
            db.session.commit()
            print(f"Updated existing reading for sensor {sensor_identifier} at {timestamp}.")
            return True
        else:
            new_reading = model(sensor_id=sensor.id, value=reading, timestamp=timestamp)
            db.session.add(new_reading)
            db.session.commit()
            print(f"Added new reading for sensor {sensor_identifier} at {timestamp}.")
            return True

    except Exception as e:
        print(f"Unable to create/update sensor reading for sensor: {sensor_identifier}, error: {e} ")
        db.session.rollback()
    return False