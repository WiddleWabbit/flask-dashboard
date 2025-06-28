# Runs the MQTT Handler and schedulers to read and publish MQTT Messages

from app import create_app
from app.models import db
from app.first_run import firstrun
from app.mqtt.mqtt_handler import MQTTHandler
from app.background_tasks.scheduler import init_scheduler, start_scheduler, shutdown_scheduler, update_mqtt_topics, get_forecast
from run import app
import atexit

app = create_app('app.config.Config')

with app.app_context():

    # Build any parts of the database not yet build
    db.create_all()
    # Run the firstrun checks in case this is the first run
    firstrun(app)

    # Initialise the MQTT Handler
    app.mqtt_handler = MQTTHandler()

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