from app import create_app
from app.models import db
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
        logging.StreamHandler(), #log to console
        logging.FileHandler("app.log") # log to file
    ]
)

# Create the app passing it the production configuration
app = create_app('app.config.Config')

if __name__ == '__main__':

    # Run the Application
    app.run(debug=True, use_reloader=False)