from app.scheduling.models import db, Schedules, DaysOfWeek
from app.func import get_setting
from app.scheduling.func import get_all_zones
from datetime import datetime, time
from app.weather.weather_handler import WeatherService, Weather
from app.sensors.func import update_reading
from app.func import get_setting
import json
import pytz

# Function will be for recieving messages
def print_message(message, app, logger):
    """
    Log the payload of an MQTT message for development and testing purposes.

    :param message: MQTT message object containing the payload to be logged.

    :return: None
    """
    print(f"{message}")
    logger.info(message.payload)

def process_mqtt(app):
    """
    Process the incoming MQTT messages by running the relevant callbacks.
    Pass through application context to give the callbacks the ability to access the database.

    :param app: Flask application instance for context.

    :return: None
    """
    with app.app_context():

        # Only proceed if we have a MQTT handler
        if app.mqtt_handler:

            # Fetch the oldest message in the queue
            message = app.mqtt_handler.get_received_message()
            while message is not None:

                topic = message[0]
                payload = message[1]
                print(f"Processing message to: {topic}, message is: {payload}")

                # Message from Sensor Topic, send to sensor callback
                if topic == get_setting("sensor_topic"):

                    result = process_sensor_message(app, topic, payload)
                    if result:
                        app.logger.info("Successfully processed message")
                    else:
                        app.logger.error("Failed to process message")

                # Fetch the next oldest message and restart loop with new message
                message = app.mqtt_handler.get_received_message()

def process_sensor_message(app, topic, message):
    """
    Process a message sent to the sensor topic. Messages are expected to be in a specific format matching:
    {"time": "2025-07-30 06:22:45", "sensors": { "0": 23.52211, "1": 24.52221 } }

    :param app: The flask application instance for database context.
    :param topic: The topic the message was received on as a string.
    :param message: The message received as a string.

    :return: True for success or False for failure.
    """
    app.logger.info(f"Received message to process: {message}")
    
    try:

        data = json.loads(message)
        naive_timestamp = datetime.strptime(data["time"], "%Y-%m-%d %H:%M:%S")

        local_tz = pytz.timezone(get_setting("timezone"))
        local_timestamp = local_tz.localize(naive_timestamp)
        utc_timestamp = local_timestamp.astimezone(pytz.UTC)

        for sensor_id, sensor_value in data["sensors"].items():

            result = update_reading(sensor_id, utc_timestamp, sensor_value)
            if result:
                app.logger.info(f"Successfully processed: {sensor_id}, value of {sensor_value}")
            else:
                app.logger.error(f"Failed to process: {sensor_id}, value of {sensor_value}")

        return True

    except Exception as e:
        app.logger.error(f"Error processing sensor message: {e}")
        return False

# Function to check time range
def is_time_in_range(start_str, end_str, now_time):
    """
    Check if the current time is within the specified start and end time range, handling overnight schedules.

    :param start_str: Start time as a string in 'HH:MM' format.
    :param end_str: End time as a string in 'HH:MM' format.
    :param now_time: Current time as a time object to check against the range.

    :return: True if now_time is within the time range, False otherwise.
    """
    start = datetime.strptime(start_str, "%H:%M").time()
    end = datetime.strptime(end_str, "%H:%M").time()
    if start <= end:
        return start <= now_time < end
    else:
        # Over midnight
        return now_time >= start or now_time < end

def update_mqtt_topics(app):
    """
    Update MQTT topic subscriptions for the sensor topic.

    :param app: Flask application instance for context.

    :return: None
    """
    with app.app_context():

        if app.mqtt_handler:
            subscribed_topics = app.mqtt_handler.get_subscribed_topics()
            sensor_topic = get_setting("sensor_topic")
            if sensor_topic:
                if sensor_topic not in subscribed_topics:
                    app.logger.info(f"Sensor topic {sensor_topic} not in subscribed topics {subscribed_topics}. Subscribing...")
                    app.mqtt_handler.unsubscribe_all()
                    app.mqtt_handler.subscribe(topic=sensor_topic, callback=print_message)
                else:
                    app.logger.info(f"Sensor topic up to date. Doing nothing.")
        else:
            app.logger.error(f"No MQTT Handler.")

def is_weather_compatible(schedule, threshold, logger):
    """
    Check if the given schedule's weather_dependent means a schedule should be active today.
    
    :param schedule: Schedule object with start (string 'HH:MM') and weather_dependent (int: 1, 2, or 3).
    :param get_setting: Function to retrieve settings (e.g., rain_threshold).
    :param reference_date: Optional date object for the schedule; defaults to current date.
    
    :return: True if the schedule is compatible with the weather forecast, False otherwise.
    """
    if not threshold or not isinstance(threshold, float):
        logger.error(f"Error with threshold value, not valid. {threshold}")
        return False

    # If weather_dependent is 3, always return True
    if schedule.weather_dependent == 3:
        logger.info("Set to ignore weather, ignoring forecast.")
        return True
    
    # Use current date in AWST
    awst = pytz.timezone('Australia/Perth')
    schedule_date = datetime.now(awst).date()
    
    # Parse the start time string (HH:MM)
    try:
        start_time = datetime.strptime(schedule.start, "%H:%M").time()
    except ValueError:
        logger.error("Invalid schedule time format.")
        return False
    
    # Combine date and time for timezone-aware datetime in AWST
    schedule_datetime = datetime.combine(schedule_date, start_time)
    schedule_datetime = awst.localize(schedule_datetime)
    
    # Convert day's start and end to UTC for querying Weather table
    start_of_day = datetime.combine(schedule_date, time.min)
    end_of_day = datetime.combine(schedule_date, time.max)
    start_of_day_awst = awst.localize(start_of_day)
    end_of_day_awst = awst.localize(end_of_day)
    start_of_day_utc = start_of_day_awst.astimezone(pytz.UTC)
    end_of_day_utc = end_of_day_awst.astimezone(pytz.UTC)
    
    # Query weather forecasts for the schedule's day in UTC
    weather_forecasts = db.session.query(Weather).filter(
        Weather.timestamp >= start_of_day_utc,
        Weather.timestamp <= end_of_day_utc
    ).all()
    
    # If no forecasts are available, return False
    if not weather_forecasts:
        return False
    
    # Sum the rainfall for the day
    total_rainfall = sum(forecast.rainfall for forecast in weather_forecasts)
    
    # For weather_dependent == 1, return True only if no rainfall is forecast
    if schedule.weather_dependent == 1:
        if total_rainfall == 0.0:
            logger.info("Requires no rainfall. No rainfall forecast.")
            return True
        else:
            logger.info("Requires no rainfall. There is rainfall forecast.")
            return False
    
     # For weather_dependent == 2, return True if total rainfall is less than the threshold
    if schedule.weather_dependent == 2:
        if total_rainfall < threshold:
            logger.info(f"Requires less than {threshold} rainfall. Forecast amount {total_rainfall}. Run schedule.")
            return True
        else:
            logger.info(f"Requires less than {threshold} rainfall. Forecast amount {total_rainfall} is more. Do not run.")
            return False
    
    # Default case: invalid weather_dependent value
    return False

def is_schedule_active(app):
    """
    Determine active schedules based on current time, day, and weather compatibility.

    :param app: Flask application instance for context.

    :return: List of active schedules that are compatible with current time, day, and weather conditions, or False if no valid schedules or required settings are unavailable.
    """

    # Use app context to access database and MQTT Handler
    with app.app_context():

        # Get the relevant time, day and other settings
        now = datetime.now()
        current_time = now.time()
        day_of_week = now.strftime("%A")
        today = DaysOfWeek.query.filter_by(name=day_of_week).first()
        yesterday = DaysOfWeek.query.filter_by(id=((today.id - 2) % 7 + 1)).first()  # Get the previous day
        threshold = float(get_setting("rain_threshold"))

        # Proceed only if we have valid time, date, and settings
        if today and yesterday and current_time and threshold:
            # Find schedules that are active and run today or yesterday (for midnight-spanning schedules)
            active_schedules = Schedules.query.filter(
                Schedules.active == 1
            ).filter(
                (Schedules.days.contains(today)) | (Schedules.days.contains(yesterday))
            ).all()

            # Check if each schedule should be active
            filtered_schedules = []
            for schedule in active_schedules:
                # Convert string times (HH:MM) to time objects
                try:
                    start_time = datetime.strptime(schedule.start, "%H:%M").time()
                    end_time = datetime.strptime(schedule.end, "%H:%M").time()
                except ValueError as e:
                    app.logger.error(f"Invalid time format for schedule {schedule.id}: {e}")
                    continue

                # Check if the schedule spans midnight (end time is earlier than start time)
                if end_time < start_time:
                    # Schedule crosses midnight
                    if today in schedule.days:
                        # Case 1: Current time is after start time (before midnight)
                        if current_time >= start_time:
                            if is_weather_compatible(schedule, threshold, app.logger):
                                filtered_schedules.append(schedule)
                    if yesterday in schedule.days:
                        # Case 2: Current time is before end time (after midnight)
                        if current_time <= end_time:
                            if is_weather_compatible(schedule, threshold, app.logger):
                                filtered_schedules.append(schedule)
                else:
                    # Schedule does not cross midnight, check if today is in the schedule
                    if today in schedule.days and is_time_in_range(schedule.start, schedule.end, current_time):
                        if is_weather_compatible(schedule, threshold, app.logger):
                            filtered_schedules.append(schedule)

            return filtered_schedules if filtered_schedules else False
        else:
            app.logger.error("Unable to fetch time, date, or required settings...")
            return False

def build_mqtt_update(app, active_schedules):
    """
    Build JSON data for MQTT update based on active schedules and zones.

    :param app: Flask application instance for context.
    :param active_schedules: List of active schedules to determine solenoid states.

    :return: JSON string containing MQTT update data with action and solenoid states, or False if no zones are configured or JSON creation fails.
    """

    # Use app context to access database and MQTT Handler
    with app.app_context():
    
        # Get all the zones and the watering topic
        zones = get_all_zones()
        if not zones:
            app.logger.error("No zones configured, no solenoids to publish MQTT updates for...")
            return False
        
        # Prepare Variables
        inactive_solenoids = []
        active_solenoids = []

        # No active schedules
        if not active_schedules:
            # Set pump action
            action = "stop"
            # Set all solenoids inactive
            for zone in zones:
                inactive_solenoids.append(zone.solenoid)

        else:
            # Set pump action
            action = "run"
            for schedule in active_schedules:
                # Get the solenoid for each zone in this schedule and add them to the list of solenoids that should be on
                for zone in schedule.zones:
                    # Ensure no doubleup's before appending
                    if zone.solenoid not in active_solenoids:
                        active_solenoids.append(zone.solenoid)
            # Mark any solenoids not already marked active, and add them to those that should be inactive.
            for zone in zones:
                if zone.solenoid not in active_solenoids:
                    inactive_solenoids.append(zone.solenoid)


        # Build the JSON Data and send to MQTT Watering Topic
        data = {
            "action": action,
            "open": active_solenoids,
            "close": inactive_solenoids
        }
        json_data = json.dumps(data)
        return json_data if json_data else False

def send_mqtt_update(app, json_data):
    """
    Publish MQTT update with the provided JSON data to the configured watering topic.

    :param app: Flask application instance for context.
    :param json_data: JSON data to be published via MQTT.

    :return: None
    """

    # Use app context to access database and MQTT Handler
    with app.app_context():

        # Get the watering topic to publish to
        watering_topic = get_setting("watering_topic")

        if not watering_topic:
            app.logger.error("No watering topic configured to publish to. Unable to publish MQTT Update.")
            return

        if not json_data:
            app.logger.error("Invalid JSON var submitted, unable to publish to MQTT.")
            return

        # Publish the MQTT Update
        app.logger.info(json_data)
        publish_status = app.mqtt_handler.publish(watering_topic, json_data, 1)
        if not publish_status:
            app.logger.error("Error publishing MQTT update.")

def mqtt_updates(app):
    """
    Publish MQTT updates based on active schedules.

    :param app: Flask application instance for context.

    :return: None
    """

    # Use app context to access database and MQTT Handler
    with app.app_context():

        # Don't proceed if not connected
        if not app.mqtt_handler or not app.mqtt_handler.is_connected():
            app.logger.error("No MQTT Handler, or MQTT not connected. Skipping..")
            return

        # Check for active schedules
        active_schedules = is_schedule_active(app)
        if not active_schedules:
            app.logger.info("No active schedules.")

        # Build the MQTT Update JSON
        json_data = build_mqtt_update(app, active_schedules)
        if not json_data:
            app.logger.error("Invalid json returned from build. Skipping publishing...")
            return
        
        # Send the MQTT update
        send_mqtt_update(app, json_data)

def get_forecast(app):
    """
    Fetch the weather forecast and save it to the database.

    :param app: Flask application instance for context.

    :return: True if weather data is successfully fetched and saved to the database, False otherwise.
    """
    with app.app_context():
        try:
            with WeatherService() as collector:
                weather_data = collector.fetch_weather()
                if weather_data:
                    db_result = collector.save_to_db(weather_data, db.session)
                    if db_result:
                        app.logger.info("Successfully fetched weather and saved to database.")
                        return True
                    else:
                        app.logger.error("Failed to save weather data to database.")
                        return False
                else:
                    app.logger.error("No weather data.")
                    return False
        except Exception as e:
            app.logger.error(f"Error fetching the weather forecast and saving it: {e}")
            return False

def process_json(message, app):
    """
    Process json, read it and run the appropriate functions to handle the data received.

    :param app: Flask application instance for context.
    """
    with app.app_context():
        try:
            data = json.loads(message)
        except Exception as e:
            app.logger.error(f"Error proccessing the JSON received: {e}")

# New function and schedule to update the sunrise sunset times