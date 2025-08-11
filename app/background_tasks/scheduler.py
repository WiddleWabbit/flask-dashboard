from app.background_tasks.func import update_mqtt_topics, mqtt_updates, get_forecast, process_mqtt
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta

# Initialize the scheduler
scheduler = BackgroundScheduler()

def init_scheduler(app):
    """Initialize and configure the scheduler with jobs.

       If required set the initial start time to shortly after the schedule is made so it runs initally and
       then on it's schedule. Done like this to run them as actual schedules rather than manual runs, that
       block execution.
    """
    try:
        scheduler.add_job(
            func=update_mqtt_topics,
            trigger=IntervalTrigger(minutes=5, start_date=datetime.now() + timedelta(seconds=15)),
            id='update_mqtt_topics',
            name='Check/Update MQTT Topics',
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
            trigger=IntervalTrigger(hours=6, start_date=datetime.now() + timedelta(seconds=15)),
            id='get_forecast',
            name='Get Weather Forecast',
            replace_existing=True,
            args=[app]
        )
        scheduler.add_job(
            func=process_mqtt,
            trigger=IntervalTrigger(minutes=1, start_date=datetime.now() + timedelta(seconds=30)),
            id='process_mqtt',
            name='Process Incoming MQTT Messages',
            replace_existing=True,
            args=[app]
        )
        app.logger.info("Scheduler initialized with jobs")
    except Exception as e:
        app.logger.error(f"Error initializing scheduler: {e}")

def start_scheduler(app):
    """Start the scheduler."""
    try:
        if not scheduler.running:
            scheduler.start()
            app.logger.info("Scheduler started")
    except Exception as e:
        app.logger.error(f"Error starting scheduler: {e}")

def shutdown_scheduler(app):
    """Shutdown the scheduler gracefully."""
    try:
        if scheduler.running:
            scheduler.shutdown()
            app.logger.info("Scheduler shutdown")
    except Exception as e:
        app.logger.error(f"Error shutting down scheduler: {e}")