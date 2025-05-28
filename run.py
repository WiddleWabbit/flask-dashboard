from app import create_app, db
from app.models import Users, Settings, Groups, Schedules, Zones, DaysOfWeek, schedule_days, zone_schedules

app = create_app()

with  app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)