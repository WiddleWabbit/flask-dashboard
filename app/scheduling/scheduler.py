from .models import db, Groups, Schedules, Zones, DaysOfWeek, schedule_days, zone_schedules
from ..models import Settings
from ..func import get_setting
from .func import get_all_days
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
def print_test(message):
    logger.info(message.payload)

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
                    app.mqtt_handler.subscribe(topic=sensor_topic, callback=print_test)
                else:
                    logger.info(f"Sensor topic up to date. Doing nothing.")
        else:
            logger.error(f"No MQTT Handler.")

# Function to check is any schedules are active
def is_schedule_active(app):

    with app.app_context():
        now = datetime.now()
        current_time = now.time()
        days = get_all_days()
        day_of_week = now.strftime("%A")
        today = DaysOfWeek.query.filter_by(name=day_of_week).first()
        watering_topic = get_setting("watering_topic")

        # Add weather
        # Add time
        # Confirm receipt of published information
        # Add turn off solenoid logic?

        # Microcontroller must stop all not in solenoid list each time

        if today and current_time and app.mqtt_handler and watering_topic:
            
            if app.mqtt_handler.is_connected():
                active_schedules = Schedules.query.filter(Schedules.active==1).filter(Schedules.days.contains(today)).all()
                solenoids = []
                for schedule in active_schedules:

                    logger.info(f"Schedule {schedule.id} starts at {schedule.start} and runs till {schedule.end}")
                    for zone in schedule.zones:
                        solenoids.append(zone.solenoid)
                        logger.info(f"Adding Schedules, Zone Solenoid: {zone.solenoid}")

                data = {
                    "action": "run",
                    "solenoids": solenoids
                }
                json_data = json.dumps(data)
                app.mqtt_handler.publish(watering_topic, json_data, 1)

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
            trigger=IntervalTrigger(seconds=30),
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