# Import the required libraries
from datetime import datetime, time
import pytz
from werkzeug.security import generate_password_hash
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from .models import db, Users, Settings
from .scheduling.models import Groups, Schedules, Zones, DaysOfWeek, schedule_days, zone_schedules
from .func import *
from .scheduling.func import get_all_zones
from app.reports.models import Report

def firstrun(app):

    with app.app_context():

        # Create a default user if none exist
        user_exists = Users.query.first()
        if not user_exists:
            password = "admin"
            hashed_password=generate_password_hash(password,method="pbkdf2:sha256")
            admin_user = Users(username="admin",password=hashed_password,firstname="Admin",lastname="User",email="test@test.com")
            db.session.add(admin_user)
            db.session.commit()

        # Create all the days of the week if they don't exist
        # Create in this order to match datetime index list
        days = [
            "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
        ]
        for day in days:
            if not DaysOfWeek.query.filter_by(name=day).first():
                db.session.add(DaysOfWeek(name=day))
        db.session.commit()

        # Add a single default zone if none exist
        all_zones = get_all_zones()
        if not all_zones:
            db.session.add(Zones(name="Zone 1", solenoid=1))
            db.session.commit()

        # Add a single default group if none exist
        groups = Groups.query.all()
        if not groups:
            db.session.add(Groups(name="Group 1"))
            db.session.commit()

        # Add a single default inactive schedule if none exist
        schedules = Schedules.query.all()
        if not schedules:
            group = Groups.query.first()
            new_sch = Schedules(group=group.id, start="05:00", end="05:10", active=0, weather_dependent=0)
            db.session.add(new_sch)
            db.session.commit()

        # Create a default rainfall threshold
        rain_threshold = Settings.query.filter_by(setting="rain_threshold").first()
        if not rain_threshold:
            def_rain_threshold = "3.0"
            db.session.add(Settings(setting="rain_threshold", value=def_rain_threshold))
            db.session.commit() 

        # Create default latitude and longitude if none exist
        lat_exists = Settings.query.filter_by(setting="latitude").first()
        long_exists = Settings.query.filter_by(setting="longitude").first()
        if not lat_exists:
            lat = "-31.889105"
            db.session.add(Settings(setting="latitude", value=lat))
            db.session.commit()
        if not long_exists:
            long = "116.04647"
            db.session.add(Settings(setting="longitude", value=long))
            db.session.commit()

        # Create the timezone setting if it doesn't exist
        timezone = Settings.query.filter_by(setting="timezone").first()
        if not timezone:
            timezone = 'Australia/Perth'
            db.session.add(Settings(setting="timezone", value=timezone))
        
        # Create the sunrise and sunset settings if they don't exist
        # sunrise_exists = Settings.query.filter_by(setting="sunrise_iso").first()
        # sunset_exists = Settings.query.filter_by(setting="sunset_iso").first()
        # if not sunrise_exists:
        #     now = datetime.now(pytz.timezone(timezone))
        #     sixam_naive = datetime.combine(now.date(), time(6, 0, 0))
        #     sixam_perth = pytz.timezone(timezone).localize(sixam_naive)
        #     sixam_utc = sixam_perth.astimezone(pytz.utc)
        #     sunrise_iso = sixam_utc.isoformat()
        #     db.session.add(Settings(setting="sunrise_iso", value=sunrise_iso))
        #     db.session.commit()
        # if not sunset_exists:
        #     now = datetime.now(pytz.timezone(timezone))
        #     sixpm_naive = datetime.combine(now.date(), time(18, 0, 0))
        #     sixpm_perth = pytz.timezone(timezone).localize(sixpm_naive)
        #     sixpm_utc = sixpm_perth.astimezone(pytz.utc)
        #     sunset_iso = sixpm_utc.isoformat()
        #     db.session.add(Settings(setting="sunset_iso", value=sunset_iso))
        #     db.session.commit()

        if not Report.query.first():
            reports = [
                Report(name="Weather Report", template_file="reports/weather_report.html", js_file="js/reports/weather_report.js", active=1, position=1)
            ]
            db.session.bulk_save_objects(reports)
            db.session.commit()