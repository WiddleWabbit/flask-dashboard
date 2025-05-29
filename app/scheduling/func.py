# Import the required libraries
import html
from datetime import datetime, time
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import requests
from .models import Groups, Schedules, Zones, DaysOfWeek, schedule_days, zone_schedules
from .. import db

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