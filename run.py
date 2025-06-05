from app import create_app
from app.models import db

#from apscheduler.schedulers.background import BackgroundScheduler
#from apscheduler.triggers.cron import CronTrigger


# Set explicit types for all functions

# Notes
# - Finish Unit Test
# - New Setup DB Function for app
# - More Orthogonal & More Functions
# - Better error handling in zones
# - Subfolders for templates
# - Coupling with global settings like timezone to be rectified
# - DateTime incorrect on CreatedAt, Needs to be fixed to be UTC always

# Create the app passing it the production configuration
app = create_app('app.config.Config')

with  app.app_context():

    # Create the database (doesn't overwrite existing tables etc.)
    db.create_all()

    # Run the first run setup to create base values etc.
    from app.first_run import firstrun
    firstrun(app)

if __name__ == '__main__':
    app.run(debug=True)