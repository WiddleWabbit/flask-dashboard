from app import create_app
from app.models import db
import atexit
import os
import logging

# Notes
# - Finish Unit Test
# - Cleanup Logging
# - DateTime incorrect on CreatedAt, Needs to be fixed to be UTC always
# - Graph to show watering times
# - History Table to show active times etc in past.

# Configure the root logger
logging.basicConfig(
    level=logging.DEBUG,  # Set the logging level to DEBUG to capture all messages
    format='%(asctime)s - %(levelname)s - %(message)s',  # Optional: Define log message format
    handlers=[
        logging.FileHandler("app.log"),  # Output logs to a file named 'example.log'
        logging.StreamHandler()  # Output logs to console
    ]
)

# Create the app passing it the production configuration
app = create_app('app.config.Config')

if __name__ == '__main__':

    # Run the Application
    app.run(debug=True, use_reloader=False)