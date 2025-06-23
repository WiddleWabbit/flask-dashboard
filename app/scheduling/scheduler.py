from .models import db, Groups, Schedules, Zones, DaysOfWeek, schedule_days, zone_schedules
from ..models import Settings
from ..func import get_setting
from .func import get_all_days, get_all_zones
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, time
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
def is_mqtt_setup(app):
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

    # The MQTT handler is a property of the app, so we use app context
    with app.app_context():

        # Get the relevant time and day
        now = datetime.now()
        current_time = now.time()        
        days = get_all_days()
        day_of_week = now.strftime("%A")
        today = DaysOfWeek.query.filter_by(name=day_of_week).first()
        # Get all the zones and the watering topic
        zones = get_all_zones()
        watering_topic = get_setting("watering_topic")
        # Prepare Variables
        inactive_solenoids = []
        active_solenoids = []
        action = "stop"

        # Proceed only if we have a valid time, date, have access to the MQTT class and a watering MQTT topic is configured
        if today and current_time and app.mqtt_handler and watering_topic:
            # Require MQTT to be connected to proceed
            if app.mqtt_handler.is_connected():

                # Find the schedules that run today and are active
                active_schedules = Schedules.query.filter(Schedules.active==1).filter(Schedules.days.contains(today)).all()
                # Check if each schedule should be active according to it's time
                for schedule in active_schedules:
                    if is_time_in_range(schedule.start, schedule.end, current_time):
                        action = "run"
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
                app.mqtt_handler.publish(watering_topic, json_data, 1)
            # If MQTT not connected skip
            else:
                logger.warning("MQTT not currently connected. Skipping...")

def send_mqtt_updates():
    if is_schedule_active():
        print("active")

        


# Initialize the scheduler
scheduler = BackgroundScheduler()

def example_job():
    """Example background job."""
    logger.info("Running example job")

def init_scheduler(app):
    """Initialize and configure the scheduler with jobs."""
    try:
        scheduler.add_job(
            func=is_mqtt_setup,
            trigger=IntervalTrigger(minutes=5),
            id='is_mqtt_setup',
            name='Check if MQTT is Setup',
            replace_existing=True,
            args=[app]
        )
        scheduler.add_job(
            func=is_schedule_active,
            trigger=IntervalTrigger(minutes=1),
            id='is_schedule_active',
            name='Check if any Schedule Should be Active',
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