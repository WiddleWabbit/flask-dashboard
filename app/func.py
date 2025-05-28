# Import the required libraries
import os
import html
from datetime import datetime, time
import pytz
from flask import Blueprint, Flask, request, render_template, url_for, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import requests
from .models import db, Users, Settings, Groups, Schedules, Zones, DaysOfWeek, schedule_days, zone_schedules
from . import db


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
    #with app.app_context():
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
