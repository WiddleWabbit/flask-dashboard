"""
Refactor Todo: 

- Function to format date data from API.
- Functions to create non existing on startup.
- Split into multiple files.
- Make all functions explicitly require certain variable types

Next Up:

- Ensure that zones repopulate with data via js if they were existing before
- Make update_sun_times run regularly via cron. - tested not implemented
- Setup schedules form.
- Defaults for other sun times
- Add Max characters to inputs to match db

Other:
- Build/Publish automatically when pushed to branch
- Auto pull regularly on pi.




SCHEDULES NEED A NAME
FORM NEEDS TO INCLUDE ACTIVE AND WEATHER DEPENDENT



Notes:
DB stores all datetime's as ISO UTC.
DB stores all time's as strings

"""



# Import the required libraries
import os
import html
from datetime import datetime, time
import pytz
from flask import Flask, request, render_template, url_for, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import requests

# Create the application
app = Flask(__name__)

# Setup DB Configuration
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "aXZ!#fl2IlR4ka6n**f6D7e8*F92#D4nf"

# Initialise SQL Alchemy and Login Manager
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# User Database Model
class Users(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)
    firstname = db.Column(db.String(250), nullable=False)
    lastname = db.Column(db.String(250), nullable=False)
    email = db.Column(db.String(250), unique=True, nullable=False)
    created_at = db.Column(db.String(60), nullable=False, default=datetime.now(pytz.utc))

    def __repr__(self):
        return f'<{self.username}>'

# Settings Database Model
class Settings(db.Model):
    __tablename__ = "settings"
    id = db.Column(db.Integer, primary_key=True, unique=True)
    setting = db.Column(db.String(250), unique=True, nullable=False)
    value = db.Column(db.String(250), unique=False, nullable=False)

    def __repr__(self):
        return f'<{self.setting}>'


# Association table for many-to-many relationship between Zones and Schedules
zone_schedules = db.Table(
    'zone_schedules',
    db.Column('zone_id', db.Integer, db.ForeignKey('zones.id'), primary_key=True),
    db.Column('schedule_id', db.Integer, db.ForeignKey('schedules.id'), primary_key=True)
)

# Association table for many-to-many relationship between Schedules and DaysOfWeek
schedule_days = db.Table(
    'schedule_days',
    db.Column('schedule_id', db.Integer, db.ForeignKey('schedules.id'), primary_key=True),
    db.Column('day_id', db.Integer, db.ForeignKey('days_of_week.id'), primary_key=True)
)


# DaysOfWeek Database Model
class DaysOfWeek(db.Model):
    __tablename__ = "days_of_week"
    id = db.Column(db.Integer, primary_key=True, unique=True)
    name = db.Column(db.String(20), unique=True, nullable=False)

    def __repr__(self):
        return f'<{self.name}>'

# Schedule Groups Database Model
class Groups(db.Model):
    __tablename__ = "groups"
    id = db.Column(db.Integer, primary_key=True, unique=True)
    name = db.Column(db.String(100), unique=False)
    schedules = db.relationship(
        'Schedules',
        lazy=True,
        backref=db.backref('groups', lazy=True),
        cascade="all, delete"
    )

    def __repr__(self):
        return f'<{self.name}>'


# Zones Database Model
class Zones(db.Model):
    __tablename__ = "zones"
    id = db.Column(db.Integer, primary_key=True, unique=True)
    name = db.Column(db.String(250), nullable=False)
    description = db.Column(db.String(250), nullable=True)
    solenoid = db.Column(db.Integer, nullable=False, unique=True)
    created_at = db.Column(db.String(60), nullable=False, default=datetime.now(pytz.utc))
    schedules = db.relationship(
        'Schedules',
        secondary=zone_schedules,
        lazy=True,
        backref=db.backref('zones', lazy=True),
        cascade="all, delete"
    )

    def __repr__(self):
        return f'<{self.name}>'

# Schedules Database Model
class Schedules(db.Model):
    __tablename__ = "schedules"
    id = db.Column(db.Integer, primary_key=True, unique=True)
    group = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
    start = db.Column(db.String(50), nullable=False)
    end = db.Column(db.String(50), nullable=False)
    active = db.Column(db.Integer, nullable=False)
    weather_dependent = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.String(60), nullable=False, default=datetime.now(pytz.utc))
    days = db.relationship(
        'DaysOfWeek', 
        secondary=schedule_days,
        lazy=True,
        backref=db.backref('schedules', lazy=True))

    def __repr__(self):
        return f'<{self.id}>'


def get_user(username):
    """
    Return the user object from the database by name.

    :param username: The username of the user to fetch.
    :return: The user object.
    """
    try:
        user = Users.query.filter_by(username=username).first()
        return user if user else None
    except Exception as e:
        print(f"Unable to get user from database: {e}")
    return None

def update_user(username, setting, data):
    """
    Update the specified user in the database with the provided data.

    :param username: The username to update.
    :param setting: The setting for the user to update.
    :param data: The value to update the setting to.
    :return: True for success, False for failure.
    """
    try:
        user = get_user(username)
        if user and hasattr(user, setting):
            setattr(user, setting, data)
            db.session.commit()
            return True
        else:
            print(f"User not found or invalid setting: {setting}")
    except Exception as e:
        print(f"Unable to update user: {e}")
    return False

def get_setting(setting_name):
    """
    Return the value of a setting from the database by name.

    :param setting_name: Name of the setting.
    :return: The value of the setting.
    """
    try:
        setting = Settings.query.filter_by(setting=setting_name).first()
        return setting.value if setting else None
    except Exception as e:
        print(f"Unable to get setting from database: {e}")
    return None

def set_setting(setting_name, value):
    """
    Set a value for a setting the database, will be created if it doesn't exist or updated if it does.

    param: setting_name: The name of the setting to set as a string.
    param: The value to set for the setting.
    :return: True for success, False for failure.
    """
    try:
        setting = Settings.query.filter_by(setting=setting_name).first()
        if setting:
            setting.value = value
        else:
            setting = Settings(setting=setting_name, value=value)
            db.session.add(setting)
        db.session.commit()
        return True
    except Exception as e:
        print(f"Unable to set setting: {e}")
    return False

def get_zone(id):
    """
    Retrieve a zone from the database by its ID.

    :param id: The ID of the zone to retrieve.
    :return: The zone object if found, otherwise None.
    """
    try:
        zone = Zones.query.filter_by(id=id).first()
        return zone if zone else None
    except Exception as e:
        print(f"Unable to get zone from database: {e}")
    return None

def get_all_zones():
    """
    Retrieve all zones from the database.

    :return: A list of all zone objects if any exist, otherwise None.
    """
    try:
        zones = Zones.query.all()
        return zones if zones else None
    except Exception as e:
        print(f"Unable to get all zones from database: {e}")
    return None

def update_zone(id, name, desc, solenoid):
    """
    Create or update a zone in the database.

    If a zone with the given ID exists, its name, description, and solenoid are updated.
    If it does not exist, a new zone is created with the provided values.

    :param id: The ID of the zone.
    :param name: The name of the zone.
    :param desc: The description of the zone.
    :param solenoid: The solenoid number for the zone.
    :return: True for success, False for failure.
    """
    try:
        zone = Zones.query.filter_by(id=id).first()
        if zone:
            zone.name = name
            zone.description = desc
            zone.solenoid = solenoid
        else:
            zone = Zones(id=id, name=name, description=desc, solenoid=solenoid)
            db.session.add(zone)
        db.session.commit()
        return True
    except Exception as e:
        print(f"Unable to update zone: {e}")
    return False

def delete_zone(id):
    """
    Delete a zone from the database by its ID.

    :param id: The ID of the zone to delete.
    :return: True if the zone was deleted successfully, False otherwise.
    """
    try:
        zone = Zones.query.filter_by(id=id).first()
        if zone:
            db.session.delete(zone)
            db.session.commit()
            return True
        else:
            return False
    except Exception as e:
        print(f"Unable to delete zone: {id}, error: {e}")
    return False

def format_isotime(time, format="%I:%M %p"):
    """
    Reformat time from ISO format to a time object

    :param time: Time string in ISO format.
    :param format: Format to output in, default is %I:%M %p
    :return String in specified output format
    """
    try:
        time_obj = datetime.fromisoformat(time)
        local_time = time_obj.astimezone(pytz.timezone(get_setting('timezone')))
        return local_time.strftime(format)
    except Exception as e:
        print(f"Error reformatting isotime: {e}")

def to_isotime(local_time, input_format="%Y-%m-%d %H:%M:%S"):
    """
    Convert local time string to ISO format in UTC time

    :param local_time: Time string in local timezone.
    :param input_format: Format of the input string, default is "%Y-%m-%d %H:%M:%S"
    :return: ISO 8601 string in UTC.
    """
    try:
        # Parse the local time string to a naive datetime object
        naive_dt = datetime.strptime(local_time, input_format)
        local_tz = pytz.timezone(get_setting('timezone'))
        local_dt = local_tz.localize(naive_dt)
        # Convert to UTC
        utc_dt = local_dt.astimezone(pytz.utc)
        return utc_dt.isoformat()
    except Exception as e:
        print(f"Error converting to ISO UTC: {e}")
    return None

def sanitise(value, expected_type=str):
    """
    Sanitise form input based on expected type.
    - For strings: strip whitespace and escape HTML.
    - For numbers: convert to int or float, or return None if invalid.
    
    :param value: The value to sanitise.
    :param expected_type: The expected variable type. Default is string.
    :return: The escaped value expected type.
    """
    if expected_type == str:
        if not isinstance(value, str):
            return value
        return html.escape(value.strip())
    elif expected_type == int:
        try:
            return int(value)
        except (ValueError, TypeError):
            return None
    elif expected_type == float:
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    return value

def update_sun_times():
    """
    Update the sunrise & sunset times in the database using apisunset.io.

    :return: True for success, False for failure.
    """
    with app.app_context():
        # Get latitude and longitude from db
        lat = get_setting("latitude")
        long = get_setting("longitude")
        url = f"https://api.sunrisesunset.io/json?lat={lat}&lng={long}&time_format=unix&timezone=Etc/UTC"
        try:
            # Handle the JSON Response
            response = requests.get(url)
            data = response.json()
            # Convert from unix timestamp to ISO
            sunrise_raw = sanitise(data["results"]["sunrise"])
            sunrise_time = datetime.fromtimestamp(int(sunrise_raw), tz=pytz.utc)
            sunrise_utc = sunrise_time.isoformat()
            # Convert from unix timestamp to ISO
            sunset_raw = sanitise(data["results"]["sunset"])
            sunset_time = datetime.fromtimestamp(int(sunset_raw), tz=pytz.utc)
            sunset_utc = sunset_time.isoformat()

            dawn_raw = sanitise(data["results"]["dawn"])
            dawn_time = datetime.fromtimestamp(int(dawn_raw), tz=pytz.utc)
            dawn_utc = sunset_time.isoformat()

            dusk_raw = sanitise(data["results"]["dusk"])
            dusk_time = datetime.fromtimestamp(int(dusk_raw), tz=pytz.utc)
            dusk_utc = dusk_time.isoformat()

            first_light_raw = sanitise(data["results"]["first_light"])
            first_light_time = datetime.fromtimestamp(int(first_light_raw), tz=pytz.utc)
            first_light_utc = first_light_time.isoformat()

            last_light_raw = sanitise(data["results"]["last_light"])
            last_light_time = datetime.fromtimestamp(int(last_light_raw), tz=pytz.utc)
            last_light_utc = last_light_time.isoformat()

            set_setting("sunrise_iso", sunrise_utc)
            set_setting("sunset_iso", sunset_utc)
            set_setting("dawn_iso", dawn_utc)
            set_setting("dusk_iso", dusk_utc)
            set_setting("first_light_iso", first_light_utc)
            set_setting("last_light_iso", last_light_utc)

            print("Sunrise and sunset times updated.")
            return True

        except Exception as e:
            print(f"Failed to update sun times: {e}")
            return False

# Prepare the application
with app.app_context():

    # Create the database, does not create or override already existing
    db.create_all()
    
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

    zones = get_all_zones()
    if not zones:
        db.session.add(Zones(name="Zone 1", solenoid=1))
        db.session.commit()

    groups = Groups.query.all()
    if not groups:
        db.session.add(Groups(name="Group 1"))
        db.session.commit()

    schedules = Schedules.query.all()
    if not schedules:
        group = Groups.query.first()
        zone = Zones.query.first()
        days = DaysOfWeek.query.all()
        day = days[2]
        new_sch = Schedules(group=group.id, start="23:59", end="00:05", active=0, weather_dependent=0)
        new_sch.days.append(day)
        new_sch.zones.append(zone)
        db.session.add(new_sch)
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
    sunrise_exists = Settings.query.filter_by(setting="sunrise_iso").first()
    sunset_exists = Settings.query.filter_by(setting="sunset_iso").first()
    if not sunrise_exists:
        now = datetime.now(pytz.timezone(timezone))
        sixam_naive = datetime.combine(now.date(), time(6, 0, 0))
        sixam_perth = pytz.timezone(timezone).localize(sixam_naive)
        sixam_utc = sixam_perth.astimezone(pytz.utc)
        sunrise_iso = sixam_utc.isoformat()
        db.session.add(Settings(setting="sunrise_iso", value=sunrise_iso))
        db.session.commit()
    if not sunset_exists:
        now = datetime.now(pytz.timezone(timezone))
        sixpm_naive = datetime.combine(now.date(), time(18, 0, 0))
        sixpm_perth = pytz.timezone(timezone).localize(sixpm_naive)
        sixpm_utc = sixpm_perth.astimezone(pytz.utc)
        sunset_iso = sixpm_utc.isoformat()
        db.session.add(Settings(setting="sunset_iso", value=sunset_iso))
        db.session.commit()
    
    # Uncomment to update sunrise/sunset on app startup
    #update_sun_times()

# Start the scheduler
#scheduler = BackgroundScheduler()
#scheduler.add_job(
#    func=update_sun_times,
#    trigger=CronTrigger(hour=1, minute=0),
#    id='update_sun_times_daily'
#)
#scheduler.start()

# Define the user loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))


# Homepage Test Route
@app.route("/")
def home():
    return render_template('dashboard.html')

# Dashboard Route
@app.route("/dashboard")
@login_required
def dashboard():
    return render_template('dashboard.html')

# Configuration Route
@app.route("/configuration", methods=["GET", "POST"])
def configuration():

    if request.method == "POST":

        if not current_user.is_authenticated:
            flash('You need to login to make modifications.', 'danger')
            return redirect(url_for("schedules"))
        
        lat = sanitise(request.form.get("latitude"), float)
        long = sanitise(request.form.get("longitude"),float)
        if not lat and not long:
            flash('Nothing input for latitude or longitude.', 'danger')
            return redirect(url_for("schedules"))
        if lat:
            set_setting("latitude", lat)
        if long:
            set_setting("longitude", long)

        flash("You've successfully updated the coordinates", 'success')
        return redirect(url_for("configuration"))

    timezone = get_setting("timezone")

    latitude = get_setting("latitude")
    longitude = get_setting("longitude")

    times = {
        "sunrise": format_isotime(get_setting("sunrise_iso")),
        "sunset": format_isotime(get_setting("sunset_iso")),
        "dawn": format_isotime(get_setting("dawn_iso")),
        "dusk": format_isotime(get_setting("dusk_iso")),
        "first_light": format_isotime(get_setting("first_light_iso")),
        "last_light": format_isotime(get_setting("last_light_iso"))
    }

    return render_template('configuration.html', timezone = timezone, times = times, lat = latitude, long = longitude)

# Zones Route
@app.route("/zones", methods=["GET", "POST"])
def zones():

    if request.method == "POST":

        if request.args.get("form") == "update_zones":
            
            submission = {}
            fields = request.form.items()

            if fields:

                fields = request.form.items()

                # Should be a function
                numbers = set()
                for key, value in fields:
                    if "-" in key:
                        suffix = key.rsplit("-", 1)[-1]
                        if suffix.isdigit():
                            numbers.add(suffix)
                zones = len(numbers)

                # Update submitted zones
                for i in range(1, zones + 1):

                    id = sanitise(request.form.get(f"id-{i}"))
                    name = sanitise(request.form.get(f"name-{i}"))
                    desc = sanitise(request.form.get(f"description-{i}"))
                    solenoid = sanitise(request.form.get(f"solenoid-{i}"))

                    update_zone(id, name, desc, solenoid)

                # Check for unsubmitted zones and delete
                all_zones = get_all_zones()
                if all_zones:
                    if len(all_zones) > zones:

                        # Starting from zone following last zone submitted
                        next_zone_id = zones + 1
                        while next_zone_id <= len(all_zones):

                            delete_zone(next_zone_id)
                            next_zone_id = next_zone_id + 1

                flash("Successfully updated zones.", 'success')
                return redirect(url_for("zones"))

            else:
                
                flash('Empty form submitted', 'danger')
                return redirect(url_for("zones"))

    

    zones = get_all_zones()
    if not zones:
        zones = [{"id":1, "name":"", "description":"", "solenoid":""}]
    
    return render_template('zones.html', zones=zones)

# Schedules Route
@app.route("/schedules", methods=["GET", "POST"])
def schedules():

    groups = Groups.query.all()
    zones = get_all_zones()
    days_of_week = DaysOfWeek.query.all()

    # Create a dict of schedule durations by schedule id
    schedule_durations = {}
    all_schedules = Schedules.query.all()
    for sched in all_schedules:
        try:
            start_dt = datetime.strptime(sched.start, "%H:%M")
            end_dt = datetime.strptime(sched.end, "%H:%M")
            # Handle overnight schedules
            if end_dt < start_dt:
                end_dt = end_dt.replace(day=start_dt.day + 1)
            duration = (end_dt - start_dt).seconds // 60
            schedule_durations[sched.id] = duration
        except Exception as e:
            schedule_durations[sched.id] = None

    return render_template('schedules.html', groups=groups, days=days_of_week, zones=zones, schedule_durations=schedule_durations)

# Login Route
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":

        username = sanitise(request.form.get("username"))
        password = sanitise(request.form.get("password"))

        user = get_user(username)

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("dashboard"))
        else:
            flash('Invalid username or password', 'danger')
            return render_template("login.html", error="Invalid username or password")

    return render_template("login.html")

# Account Route
@app.route("/account", methods=["GET", "POST"])
@login_required
def account():

    user = get_user(username=current_user.username)
    formatted_created = format_isotime(user.created_at, "%B %d, %Y, %I:%M %p")

    if request.method == "POST":

        if request.args.get("form") == "change_password":
            current_password = sanitise(request.form.get("current_password"))
            new_password = sanitise(request.form.get("new_password"))
            new_password_conf = sanitise(request.form.get("new_password_conf"))

            if new_password != new_password_conf:
                flash('Provided new passwords do not match!', 'danger')
                return redirect(url_for("account"))

            if check_password_hash(user.password, current_password):
                hashed_password = generate_password_hash(new_password, method="pbkdf2:sha256")
                update_user(user.username, "password", hashed_password)
                flash("You've successfully updated your password.", 'success')
                return redirect(url_for("account"))
            else:
                flash('Provided new passwords do not match!', 'danger')
                return redirect(url_for("account"))

        elif request.args.get("form") == "update_details":
            current_password = sanitise(request.form.get("current_password_details"))
            username = sanitise(request.form.get("username"))
            firstname = sanitise(request.form.get("firstname"))
            lastname = sanitise(request.form.get("lastname"))
            email = sanitise(request.form.get("email"))

            if check_password_hash(user.password, current_password):
                if not username and not firstname and not lastname and not email:
                    flash("No fields submitted to change.", 'danger')
                    return redirect(url_for("account"))
                if username:
                    if get_user(username):
                        flash('Unable to update. Username already exists.', 'danger')
                        return redirect(url_for("account"))
                    update_user(user.username, "username", username)
                if firstname:
                    update_user(user.username, "firstname", firstname)
                if lastname:
                    update_user(user.username, "lastname", lastname)
                if email:
                    update_user(user.username, "email", email)

                flash("You've successfully updated your details.", 'success')
                return redirect(url_for("account"))
            else:
                flash('Password entered is incorrect!', 'danger')
                return redirect(url_for("account"))
    return render_template("account.html", user = user, created = formatted_created)

# Logout Route
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))