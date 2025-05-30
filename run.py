from app import create_app
from app.models import db

#from apscheduler.schedulers.background import BackgroundScheduler
#from apscheduler.triggers.cron import CronTrigger

# Notes
# - More Orthogonal & More Functions
# - Better error handling in zones
# - Subfolders for templates
# - Coupling with global settings like timezone to be rectified
# - DateTime incorrect on CreatedAt, Needs to be fixed to be UTC always

app = create_app('app.config.Config')

with  app.app_context():
    db.create_all()

    from app.first_run import firstrun
    firstrun(app)

if __name__ == '__main__':
    app.run(debug=True)