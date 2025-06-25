# Runs the MQTT Handler and schedulers to read and publish MQTT Messages

from app import create_app
from app.models import db
from app.mqtt.mqtt_handler import MQTTHandler
from app.scheduling.scheduler import init_scheduler, start_scheduler, shutdown_scheduler, check_mqtt_topics
from run import app
import atexit

app = create_app('app.config.Config')

with app.app_context():

    db.create_all()

    # Initialise the MQTT Handler
    app.mqtt_handler = MQTTHandler()

    # Setup MQTT with anything already configured
    check_mqtt_topics(app)

    # Initialize and start the scheduler
    init_scheduler(app)
    start_scheduler()

    # Register scheduler shutdown when app exits
    atexit.register(shutdown_scheduler)

    # Keep the process alive
    import time
    try:
        while True:
            time.sleep(120)
    except KeyboardInterrupt:
        print("Scheduler stopped.")