from app.sensors.models import Sensors, db, CalibrationModeData, WaterDepth, Temperature
from sqlalchemy import func

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

def convert_waterdepth(value):
    """
    Function to convert the water depth sensor value to the value stored in the database.

    :param value:The value returned by the water depth sensor.

    :return: The converted value as a float.
    """
    # Define the ranges
    min_voltage = 0.48
    max_voltage = 2.4
    min_depth = 0
    max_depth = 200
    # Calculate the slope
    slope = (max_depth - min_depth) / (max_voltage - min_voltage)
    # Apply linear interpolation
    depth = slope * (value - min_voltage)
    # Step 4: Clamp the output to the valid range
    if depth < min_depth:
        return float(min_depth)
    elif depth > max_depth:
        return float(max_depth)
    return depth

def convert_temperature(value):
    """
    Function to convert the temperature sensor value to the value stored in the database.

    :param value:The value returned by the temperature sensor.

    :return: The converted value as a float.
    """
    return value

def no_conversion(value):
    """
    Function to perform no conversion and merely return the raw data. For use in calibration mode.

    :param value:The value returned by the sensor being calibrated.

    :return: The same value returned.
    """
    return value

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

        # Get the model to update and the function to convert the data, calibration mode overrides normal model.
        if sensor.type == "waterdepth":
            model = WaterDepth
            conversion_function = convert_waterdepth
        elif sensor.type == "temperature":
            model = Temperature
            conversion_function = convert_temperature
        if sensor.calibration_mode == 1:
            model = CalibrationModeData
            conversion_function = no_conversion
        if not model:
            print(f"Unknown sensor type or mode for sensor {sensor_identifier}.")
            return False
        
        # Set any offset configured.
        if sensor.calibration_mode == 1:
            calibration_offset = 0.0
        else:
            calibration_offset = sensor.calibration

        # Check if a reading with the same timestamp and sensor_id already exists
        existing_reading = model.query.filter_by(sensor_id=sensor.id, timestamp=timestamp).first()

        # Either update the existing reading at this timestamp for this sensor, or add a new one if it doesn't exist.
        if existing_reading:
            existing_reading.value = conversion_function(reading + calibration_offset)
            db.session.commit()
            print(f"Updated existing reading for sensor {sensor_identifier} at {timestamp}.")
            return True
        else:
            new_reading = model(sensor_id=sensor.id, value=conversion_function(reading + calibration_offset), timestamp=timestamp)
            db.session.add(new_reading)
            db.session.commit()
            print(f"Added new reading for sensor {sensor_identifier} at {timestamp}.")
            return True

    except Exception as e:
        print(f"Unable to create/update sensor reading for sensor: {sensor_identifier}, error: {e} ")
        db.session.rollback()
    return False

def calculate_calibration_value(identifier):
    """
    Calculate the new calibration offset, based on the average of all calibration mode data submitted for this sensor identifier, 
    and the current calibration setting (as correct current value).

    :param sensor_id: The sensor identifier to calculate the value for as a string

    :return: The new offset value as a float.
    """

    # Get the sensors calibration setting (representing the current correct value)
    sensor = Sensors.query.filter_by(identifier=identifier).first()
    base_value = sensor.calibration

    # Get the average for the sensor identifier
    average = CalibrationModeData.query.filter_by(sensor_id=sensor.id).with_entities(func.avg(CalibrationModeData.value)).scalar()
    # If none, then no data to average, set calibration to 0.0
    if average == None:
        average = 0.0
    # Otherwise clear the data after fetching the average
    else:
        CalibrationModeData.query.filter_by(sensor_id=sensor.id).delete()
        db.session.commit()

    # Calculate the difference which will be the new offset and return it
    offset = base_value - average
    return offset