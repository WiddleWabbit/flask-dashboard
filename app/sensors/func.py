from app.sensors.models import Sensors, db

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