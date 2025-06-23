# Import the required libraries
import html
from datetime import datetime, time
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import requests
from .models import db, Groups, Schedules, Zones, DaysOfWeek, schedule_days, zone_schedules
from werkzeug.datastructures import MultiDict

def get_zone(id):
    """
    Retrieve a zone from the database by its ID.

    :param id: The ID of the zone to retrieve.
    :return: The zone object if found, otherwise None.
    """
    try:
        zone = Zones.query.filter_by(id=id).first()
        return zone if zone else False
    except Exception as e:
        print(f"Unable to get zone from database: {e}")
        return False
    return False

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

def get_group(id):
    """
    Retrieve a group from the database by its ID.

    :param id: The ID of the group to retrieve.
    :return: The group object if found, otherwise False.
    """
    if id and isinstance(id, int):
        try:
            group = Groups.query.filter_by(id=id).first()
            return group if group else False
        except Exception as e:
            print(f"Unable to get group from database: {e}")
            return False
    else:
        return False
    return False

def get_all_groups():
    """
    Retrieve all groups from the database.

    :return: A list of all group objects if any exist, otherwise False.
    """
    try:
        groups = Groups.query.all()
        return groups if groups else False
    except Exception as e:
        print(f"Unable to get all groups from database: {e}")
        return False
    return False

def update_group(id, name):
    """
    Create or update a group in the database.

    If a group with the given ID exists, it's name is updated.
    If it does not exist, a new group is created with the provided values.

    :param id: The ID of the zone.
    :param name: The name of the zone.
    :return: True for success, False for failure.
    """
    if not isinstance(id, int) or not isinstance(name, str):
        print('Instances supplied to update group are incorrect')
        return False
    if id < 0:
        print('ID supplied to update group is negative')
        return False
    if len(name) < 1:
        print('Group name not long enough')
        return False
    try:
        group = Groups.query.filter_by(id=id).first()
        if group:
            group.name = name
        else:
            group = Groups(id=id, name=name)
            db.session.add(group)
        db.session.commit()
        return True
    except Exception as e:
        print(f"Unable to update group: {e}")
        return False
    return False

def delete_group(id: int):
    """
    Delete a group from the database by its ID.

    :param id: The ID of the group to delete.
    :return: True if the group was deleted successfully, False otherwise.
    """
    if not isinstance(id, int):
        print('Wrong id instance type submitted for delete schedule')
        return False
    try:
        group = Groups.query.filter_by(id=id).first()
        if group:
            db.session.delete(group)
            db.session.commit()
            return True
        else:
            return False
    except Exception as e:
        print(f"Unable to delete zone: {id}, error: {e}")
    return False

def get_day(id):
    """
    Retrieve a day from the database by its ID.

    :param id: The ID of the day to retrieve.
    :return: The day object if found, otherwise False.
    """
    if id and isinstance(id, int):
        try:
            day = DaysOfWeek.query.filter_by(id=id).first()
            return day if day else False
        except Exception as e:
            print(f"Unable to get day from database: {e}")
            return False
    else:
        return False
    return False

def get_all_days():
    """
    Retrieve all days from the database.

    :return: The days objects if found, otherwise False.
    """
    try:
        days = DaysOfWeek.query.all()
        return days if days else False
    except Exception as e:
        print(f"Unable to get day from database: {e}")
        return False
    return False

def get_all_schedules():
    """
    Retrieve all schedules from the database.

    :return: A list of all schedules objects if any exist, otherwise False.
    """
    try:
        schedules = Schedules.query.all()
        return schedules if schedules else False
    except Exception as e:
        print(f"Unable to get all sschedules from database: {e}")
        return False
    return False

def update_schedule(id:int, sort_order:int, group:int, start:str, end:str, active:int, weather_dependent:int, days:list, zones:list):
    """
    Create or update a schedule in the database.

    If a schedule with the given ID exists, it is updated.
    If it does not exist, a new schedule is created with the provided values.

    :param id: The ID of the schedule. To create a new one, supply false.
    :param group: The int id of the group it is under.
    :param start: The start time in HH:MM format.
    :param end: The end time in HH:MM format.
    :param active: Whether or not this schedule is active as a boolean, 1 or 0.
    :param weather_dependent: Integer selecting the behaviour with weather.
    :param days: List of the day objects from the days of the week table representing the days this schedule is active.
    :param zones: List of zone objects from the zones table, representing the zones this schedule is active on.
    :return: True for success, False for failure.
    """
    if not isinstance(group, int) or not isinstance(end, str) or not isinstance(active, int) or not isinstance(weather_dependent, int) or not isinstance(days, list) or not isinstance(zones, list) or not isinstance(sort_order, int):
        print('Instance Invalid')
        return False
    if weather_dependent > 3 or weather_dependent < 1:
        print('Weather Dependent field invalid')
        return False
    for day in days:
        if not isinstance(day, object):
            print('Invalid Day')
            return False
    for zone in zones:
        if not isinstance(zone, object):
            print('Invalid Zone')
            return False
    if not datetime.strptime(start, "%H:%M") or not datetime.strptime(end, "%H:%M"):
        print('Invalid start or end time')
        return False
    if sort_order < 0:
        print('Invalid id or sort_order supplied')
        return False
    if not id == None:
        if not isinstance(id, int) or id < 0:
            print('Invalid ID supplied')
            return False
    try:
        if id:
            schedule = Schedules.query.filter_by(id=id).first()
            if schedule:
                schedule.group = group
                schedule.sort_order = sort_order
                schedule.start = start
                schedule.end = end
                schedule.active = active
                schedule.weather_dependent  = weather_dependent
                schedule.days = days
                schedule.zones = zones
            else:
                schedule = Schedules(id=id, sort_order = sort_order, group=group, start=start, end=end, active=active, weather_dependent=weather_dependent, days=days, zones=zones)
        else:
            schedule = Schedules(sort_order = sort_order, group=group, start=start, end=end, active=active, weather_dependent=weather_dependent, days=days, zones=zones)
            db.session.add(schedule)
        db.session.commit()
        return True
    except Exception as e:
        print(f"Unable to update schedule: {e}")
        return False
    return False

def delete_schedule(id: int):
    """
    Delete a schedule from the database by its ID.

    :param id: The ID of the schedule to delete.
    :return: True if the schedule was deleted successfully, False otherwise.
    """
    if not isinstance(id, int):
        print('Wrong id instance type submitted for delete schedule')
        return False
    try:
        schedule = Schedules.query.filter_by(id=id).first()
        if schedule:
            db.session.delete(schedule)
            db.session.commit()
            return True
        else:
            return False
    except Exception as e:
        print(f"Unable to delete zone: {id}, error: {e}")
    return False

def count_fields(fields):
    """
    Count the number of duplicate fields. Identified by a -1, -2 etc.
    
    :param fields: The fields to count as a dictionary.
    :return: The count of the number of duplicate fields as an int. Returns false on error.
    """
    try:
        # Validate fields are submitted and as a dictionary
        if not fields:
            return False

        # Count the fields
        numbers = set()
        for key, value in fields:
            if "-" in key:
                suffix = key.rsplit("-", 1)[-1]
                if suffix.isdigit():
                    numbers.add(suffix)
        num_fields = len(numbers)
        print(numbers)

        # Confirm the number of fields, or False if less than 1
        if num_fields < 1:
            return False
        else:
            return num_fields
    
    except Exception as e:
        return False
    
def add_minutes_to_time(time_str, add_minutes):
    """
    Add minutes to a HH:MM formatted string.
    
    :param time_str: The HH:MM formattted string.
    :return: The new HH:MM string, or False on error.
    """
    if not time_str or not add_minutes:
        return False
    if not datetime.strptime(time_str, "%H:%M"):
        return False
    if not isinstance(add_minutes, int):
        return False
    try:
        # Parse the time string (e.g., "23:50") into hours and minutes
        hours, minutes = map(int, time_str.split(":"))
        # Convert to total minutes since midnight
        total_minutes = hours * 60 + minutes
        # Add the specified minutes and handle midnight crossing
        total_minutes = (total_minutes + add_minutes) % (24 * 60)
        # Convert back to hours and minutes
        new_hours = total_minutes // 60
        new_minutes = total_minutes % 60
        # Format as HH:MM
        return f"{new_hours:02d}:{new_minutes:02d}"
    except Exception as e:
        print('Failed to add minutes to time')
        return False