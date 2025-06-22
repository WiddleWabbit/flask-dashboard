from .models import db, Groups, Schedules, Zones, DaysOfWeek, schedule_days, zone_schedules
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



def print_test():
    logger.info("Received test message")

# Function to check is MQTT is setup?
def is_mqtt_setup():
    #################
    print()
    #################

# Function to check is any schedules are active
def is_schedule_active():
    current_time = datetime.now().time()
    active_schedules = Schedules.query.filter_by(active=1).all()
    for schedule in active_schedules:

        print(schedule)
    return True

def send_mqtt_updates():
    if is_schedule_active():
        print("active")

        


# Initialize the scheduler
scheduler = BackgroundScheduler()

def example_job():
    """Example background job."""
    logger.info("Running example job")

def init_scheduler():
    """Initialize and configure the scheduler with jobs."""
    try:
        # Add jobs here
        scheduler.add_job(
            func=example_job,
            trigger=IntervalTrigger(seconds=30),  # Runs every 30 seconds
            id='example_job',
            name='Example recurring job',
            replace_existing=True
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