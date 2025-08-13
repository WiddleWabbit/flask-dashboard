# Sensors Module

This module provides the backend logic, database models, and HTTP routes for managing sensors in the flask application. It supports CRUD operations for sensors, calibration workflows, and storage of sensor readings (e.g., water depth and temperature).

## Files Overview

- [models.py](/app/sensors/models.py): Flask-SQLAlchemy ORM models for sensors and their readings.
- [func.py](/app/sensors/func.py): Core functions for sensor CRUD, calibration, and reading management.
- [routes.py](/app/sensors/routes.py): Flask routes and form handling for the sensors admin page.

## Models

- Sensors: Represents a sensor device (name, type, identifier, calibration, etc.).
- CalibrationModeData: Stores raw readings during calibration mode.
- WaterDepth: Stores water depth readings for a sensor.
- Temperature: Stores temperature readings for a sensor.

Each reading table (including CalibrationModeData) is linked to a sensor via a foreign key.

## Sensor Flow

Sensors each have an identifier to identify them separately to their primary key (allowing them to be human readable).\
Sensor data is saved using the update_reading function. The timestamp is used as a secondary key, and data is replaced instead of added if it has the
same timestamp. \
The timestamp format should match: 'YYYY-MM-DD HH:MM:SS'\
Processing follows the below:

- Reading submitted to function
- Check for an existing reading based on timestamp, replace it if it's already existing, otherwise create a new reading
- If this sensor is in calibration mode:
  - Save the data to the CalibrationModeData table with no offset.
- If not in calibration mode
  - Add the calibration offset to the sensor reading.
  - Run the conversion function for the sensor type on the value
  - Save the converted value to the database.

Specific's can be found by examining the docstrings and functions.

## Calibration Mode Flow

Calibration mode allows the user to automatically calculate the required offset for a sensor. It requires the current correct value to be set, and is handled by storing raw values and computing offsets when calibration mode is disabled.

- When calibration mode is ticked, all sensor readings are saved in the CalibrationModeData instead of their normal table.
- When unticked the readings are averaged and converted to an offset for the sensor in question, based on the 'correct' value set in the calibration field when the box is unticked.
- Calibration mode data, is cleared on coming out of calibration mode.

## Notes

- All sensor identifiers must be unique.

## Example

To add a new sensor programmatically:

```
from app.sensors.func import update_sensor

update_sensor(
    id=None,
    name="Tank Depth",
    type="waterdepth",
    identifier="tank1",
    calibration=0.0,
    calibration_mode=0,
    sort_order=1
)
```

See docstrings for more details.