from app import create_app
from app.models import db
from app.scheduling.scheduler import init_scheduler, start_scheduler, shutdown_scheduler, is_mqtt_setup
import atexit
import os
import logging


# Notes
# - Finish Unit Test
# - DateTime incorrect on CreatedAt, Needs to be fixed to be UTC always

# Configure the root logger
logging.basicConfig(
    level=logging.DEBUG,  # Set the logging level to DEBUG to capture all messages
    handlers=[
        logging.StreamHandler()  # Output logs to console
    ]
)

# Create the app passing it the production configuration
app = create_app('app.config.Config')

# Initialise the MQTT Handler and Connect
# if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
#     mqtt_handler = MQTTHandler()

with app.app_context():

    # Create the database (doesn't overwrite existing tables etc.)
    db.create_all()

    # Run the first run setup to create base values etc.
    from app.first_run import firstrun
    firstrun(app)

if __name__ == '__main__':

    # Setup MQTT with anything already configured
    is_mqtt_setup(app)

    # Initialize and start the scheduler
    init_scheduler(app)
    start_scheduler()
    
    # Register scheduler shutdown when app exits
    atexit.register(shutdown_scheduler)

    # Run the Application
    app.run(debug=True, use_reloader=False)