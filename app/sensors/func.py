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