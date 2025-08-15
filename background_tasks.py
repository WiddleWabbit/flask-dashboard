# Runs the MQTT Handler and schedulers to read and publish MQTT Messages

from app import create_app
from app.models import db
from app.first_run import firstrun
from app.background_tasks.mqtt_handler import MQTTHandler
from app.background_tasks.scheduler import init_scheduler, start_scheduler, shutdown_scheduler, update_mqtt_topics, get_forecast
from run import app
import atexit
import logging

# Configure logging
logging.getLogger('').handlers.clear()
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("background_tasks.log", mode="a"),
        logging.StreamHandler() 
    ]
)

app = create_app('app.config.Config')

with app.app_context():

    # Build any parts of the database not yet build
    db.create_all()
    # Run the firstrun checks in case this is the first run
    firstrun(app)

    # Initialise the MQTT Handler
    app.mqtt_handler = MQTTHandler()
    app.logger = logging.getLogger(__name__)

    # Initialize and start the scheduler
    init_scheduler(app)
    start_scheduler(app)

    # Register scheduler shutdown when app exits
    atexit.register(shutdown_scheduler, app)

    # Keep the process alive
    import time
    try:
        while True:
            time.sleep(120)
    except KeyboardInterrupt:
        print("Scheduler stopped.")