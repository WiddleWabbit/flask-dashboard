from app.scheduling.models import db, Groups, Schedules, Zones, DaysOfWeek, schedule_days, zone_schedules
from app.models import Settings
from app.func import get_setting
from app.scheduling.func import get_all_days, get_all_zones
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, time
from app.weather.weather_handler import WeatherService
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Function will be for recieving messages
def print_message(message):
    logger.info(message.payload)

# Function to check time range
def is_time_in_range(start_str, end_str, now_time):
    """Check if now_time is within the start and end time (handles overnight)."""
    start = datetime.strptime(start_str, "%H:%M").time()
    end = datetime.strptime(end_str, "%H:%M").time()
    if start <= end:
        return start <= now_time < end
    else:
        # Over midnight
        return now_time >= start or now_time < end

# Function to check is MQTT is setup?
def check_mqtt_topics(app):

    # Use app context to access database and MQTT Handler
    with app.app_context():

        if app.mqtt_handler:
            subscribed_topics = app.mqtt_handler.get_subscribed_topics()
            sensor_topic = get_setting("sensor_topic")
            if sensor_topic:
                if sensor_topic not in subscribed_topics:
                    logger.info(f"Sensor topic {sensor_topic} not in subscribed topics {subscribed_topics}. Subscribing...")
                    app.mqtt_handler.unsubscribe_all()
                    app.mqtt_handler.subscribe(topic=sensor_topic, callback=print_message)
                else:
                    logger.info(f"Sensor topic up to date. Doing nothing.")
        else:
            logger.error(f"No MQTT Handler.")



# Function to check is any schedules are active
def is_schedule_active(app):

    # Add weather
    # Adjust to use MQTT Updates function, split across this for getting active schedules etc
    # Confirm receipt of published information

    # Use app context to access database and MQTT Handler
    with app.app_context():

        # Get the relevant time and day
        now = datetime.now()
        current_time = now.time()        
        days = get_all_days()
        day_of_week = now.strftime("%A")
        today = DaysOfWeek.query.filter_by(name=day_of_week).first()

        # Proceed only if we have a valid time, date, have access to the MQTT class and a watering MQTT topic is configured
        if today and current_time:

            # Find the schedules that run today and are active
            active_schedules = Schedules.query.filter(Schedules.active==1).filter(Schedules.days.contains(today)).all()

            # Check if each schedule should be active according to it's time and put it in the list if it should be
            filtered_schedules = [
                schedule for schedule in active_schedules
                if is_time_in_range(schedule.start, schedule.end, current_time)
            ]
            return filtered_schedules if filtered_schedules else False


def build_mqtt_update(app, active_schedules):

    # Use app context to access database and MQTT Handler
    with app.app_context():
    
        # Get all the zones and the watering topic
        zones = get_all_zones()
        if not zones:
            logger.error("No zones configured, no solenoids to publish MQTT updates for...")
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

    # Use app context to access database and MQTT Handler
    with app.app_context():

        # Get the watering topic to publish to
        watering_topic = get_setting("watering_topic")

        if not watering_topic:
            logger.error("No watering topic configured to publish to. Unable to publish MQTT Update.")
            return

        if not json_data:
            logger.error("Invalid JSON var submitted, unable to publish to MQTT.")
            return

        # Publish the MQTT Update
        logger.info(json_data)
        publish_status = app.mqtt_handler.publish(watering_topic, json_data, 1)
        if not publish_status:
            logger.error("Error publishing MQTT update.")

def mqtt_updates(app):

    # Use app context to access database and MQTT Handler
    with app.app_context():

        # Don't proceed if not connected
        if not app.mqtt_handler or not app.mqtt_handler.is_connected():
            logger.error("No MQTT Handler, or MQTT not connected. Skipping..")
            return

        # Check for active schedules
        active_schedules = is_schedule_active(app)
        if not active_schedules:
            logger.info("No active schedules.")

        # Build the MQTT Update JSON
        json_data = build_mqtt_update(app, active_schedules)
        if not json_data:
            logger.error("Invalid json returned from build. Skipping publishing...")
            return
        
        # Send the MQTT update
        send_mqtt_update(app, json_data)


# New function and schedule to update the sunrise sunset times

###### RUN IMMEDIATELY FIRST TIME ONLY FOR OTHER FUNCTIONS??? #########
###### LOCATION BASED, TRACK LAT & LONG OF QUERIES? ##########
###### ADD WEATHER CHECKING TO SCHEDULING ########
###### RUN FIRST RUN ON BACKGROUND_TASK FILE ########
###### CONFIRM DATE / TIME WORK OUT EASIEST QUERYING - LOCAL? #######


# Fetch the weather forecast
def get_forecast(app):
    with app.app_context():
        try:
            with WeatherService() as collector:
                weather_data = collector.fetch_weather()
                if weather_data:
                    db_result = collector.save_to_db(weather_data, db.session)
                    if db_result:
                        logger.info("Successfully fetched weather and saved to database.")
                    else:
                        logger.error("Failed to save weather data to database.")
        except Exception as e:
            logger.error(f"Error fetching the weather forecast and saving it: {e}")


# Initialize the scheduler
scheduler = BackgroundScheduler()

def example_job():
    """Example background job."""
    logger.info("Running example job")

def init_scheduler(app):
    """Initialize and configure the scheduler with jobs."""
    try:
        scheduler.add_job(
            func=check_mqtt_topics,
            trigger=IntervalTrigger(minutes=5),
            id='check_mqtt_topics',
            name='Check MQTT Topics',
            replace_existing=True,
            args=[app]
        )
        scheduler.add_job(
            func=mqtt_updates,
            trigger=IntervalTrigger(minutes=1),
            id='mqtt_updates',
            name='Send MQTT Updates',
            replace_existing=True,
            args=[app]
        )
        scheduler.add_job(
            func=get_forecast,
            trigger=IntervalTrigger(hours=12),
            id='get_forecast',
            name='Get Weather Forecast',
            replace_existing=True,
            args=[app]
        )
        logger.info("Scheduler initialized with jobs")
    except Exception as e:
        logger.error(f"Error initializing scheduler: {e}")

def start_scheduler():
    """Start the scheduler."""
    try:
        if not scheduler.running:
            scheduler.start()
            logger.info("Scheduler started")
    except Exception as e:
        logger.error(f"Error starting scheduler: {e}")

def shutdown_scheduler():
    """Shutdown the scheduler gracefully."""
    try:
        if scheduler.running:
            scheduler.shutdown()
            logger.info("Scheduler shutdown")
    except Exception as e:
        logger.error(f"Error shutting down scheduler: {e}")



# # Function to check is any schedules are active
# def is_schedule_active(app):

#     # Add weather
#     # Adjust to use MQTT Updates function, split across this for getting active schedules etc
#     # Confirm receipt of published information

#     # The MQTT handler is a property of the app, so we use app context
#     with app.app_context():

#         # Get the relevant time and day
#         now = datetime.now()
#         current_time = now.time()        
#         days = get_all_days()
#         day_of_week = now.strftime("%A")
#         today = DaysOfWeek.query.filter_by(name=day_of_week).first()
#         # Get all the zones and the watering topic
#         zones = get_all_zones()
#         watering_topic = get_setting("watering_topic")
#         # Prepare Variables
#         inactive_solenoids = []
#         active_solenoids = []
#         action = "stop"

#         # Proceed only if we have a valid time, date, have access to the MQTT class and a watering MQTT topic is configured
#         if today and current_time and app.mqtt_handler and watering_topic:
#             # Require MQTT to be connected to proceed
#             if app.mqtt_handler.is_connected():

#                 # Find the schedules that run today and are active
#                 active_schedules = Schedules.query.filter(Schedules.active==1).filter(Schedules.days.contains(today)).all()
#                 # Check if each schedule should be active according to it's time
#                 for schedule in active_schedules:
#                     if is_time_in_range(schedule.start, schedule.end, current_time):
#                         action = "run"
#                         # Get the solenoid for each zone in this schedule and add them to the list of solenoids that should be on
#                         for zone in schedule.zones:
#                             # Ensure no doubleup's before appending
#                             if zone.solenoid not in active_solenoids:
#                                 active_solenoids.append(zone.solenoid)

#                 # Mark any solenoids not already marked active, and add them to those that should be inactive.
#                 for zone in zones:
#                     if zone.solenoid not in active_solenoids:
#                         inactive_solenoids.append(zone.solenoid)

#                 # Build the JSON Data and send to MQTT Watering Topic
#                 data = {
#                     "action": action,
#                     "open": active_solenoids,
#                     "close": inactive_solenoids
#                 }
#                 json_data = json.dumps(data)
#                 app.mqtt_handler.publish(watering_topic, json_data, 1)
#             # If MQTT not connected skip
#             else:
#                 logger.warning("MQTT not currently connected. Skipping...")