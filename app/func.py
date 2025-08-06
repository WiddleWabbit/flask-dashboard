# Import the required libraries
import html
from datetime import datetime, time, timezone, timedelta
import pytz
import requests
from flask import flash
from .models import db, Users, Settings
#from . import db

def get_user(username:str):
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

def update_user(username:str, setting:str, data:str):
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
            return False
    except Exception as e:
        print(f"Unable to update user: {e}")
        return False
    return False

def get_setting(setting_name:str):
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

def set_setting(setting_name:str, value:str):
    """
    Set a value for a setting the database, will be created if it doesn't exist or updated if it does.

    param: setting_name: The name of the setting to be set as a string.
    param: The value to set for the setting as a string.
    :return: True for success, False for failure.
    """
    try:
        if type(setting_name) != str or type(value) != str:
            print("Setting or value not string")
            return False
        if len(setting_name) == 0 or len(value) == 0:
            print("Setting or value too short")
            return False
        if setting_name == None or value == None:
            print("Empty setting or value")
            return False
        setting = Settings.query.filter_by(setting=setting_name).first()
        if setting:
            setting.value = value
        else:
            new_setting = Settings(setting=setting_name, value=value)
            db.session.add(new_setting)
        db.session.commit()
        return True
    except Exception as e:
        print(f"Unable to set setting: {e}")
    return False

def format_isotime(time:str, format:str="%I:%M %p"):
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

def to_isotime(local_time:str, input_format:str="%Y-%m-%d %H:%M:%S"):
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
        return False
    return False

def timestamp_to_db(timestamp, tz=pytz.utc):
    """
    Convert a Unix timestamp to a timezone-aware datetime object for db.DateTime.
    
    :param timestamp: Int or Float, Unix timestamp (seconds since 1970-01-01 00:00:00 UTC).
    :param tz: (pytz.timezone, optional): Timezone for the timestamp. Defaults to UTC.
    :return: Timezone-aware datetime object suitable for db.DateTime.
    """
    try:
        # Convert Unix timestamp to datetime with specified timezone
        dt = datetime.fromtimestamp(timestamp, tz=tz)
        # Ensure UTC for storage consistency
        return dt.astimezone(pytz.utc)
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid Unix timestamp: {timestamp}. Error: {str(e)}")

def sanitise(value, expected_type:str=str):
    """
    Sanitise form input based on expected type.
    - For strings: strip whitespace and escape HTML.
    - For numbers: convert to int or float, or return False if invalid.
    
    :param value: The value to sanitise.
    :param expected_type: The expected variable type. Default is string.
    :return: The escaped value expected type. False on error or invalid.
    """
    if expected_type == str:
        try:
            if not isinstance(value, str):
                return False
            if not len(value.strip()) > 0:
                return False
            return html.escape(value.strip())
        except (ValueError, TypeError):
            return False
    elif expected_type == int:
        try:
            return int(value)
        except (ValueError, TypeError):
            return False
    elif expected_type == float:
        try:
            return float(value)
        except (ValueError, TypeError):
            return False
    return False

def update_status_messages(results: dict):
    """
    Accepts a dict like {'username': True, 'firstname': False, ...}
    Returns (success_msg, failure_msg) summarizing which fields were updated or failed.

    :param results: Dictionary or results with values of true or false
    :return: Dict of messages, key's are the appropriate flash category. False on error.
    """
    try:
        if not isinstance(results, dict):
            return False

        for key, val in results.items():
            if key == None or key == "":
                return False
            if not isinstance(key, str) or not isinstance(val, bool):
                return False

        success_fields = [field for field, ok in results.items() if ok]
        fail_fields = [field for field, ok in results.items() if not ok]

        messages = {}
        if success_fields:
            success_msg = "Successfully updated: " + ", ".join(success_fields) + "."
            messages["success"] = success_msg
        if fail_fields:
            failure_msg = "Failed to update: " + ", ".join(fail_fields) + "."
            messages["danger"] = failure_msg

        return messages
    except Exception as e:
        print(e)
        return False

def delete_status_messages(results: dict):
    """
    Accepts a dict like {'username': True, 'firstname': False, ...}
    Returns messages summarizing which fields were updated or failed.

    :param results: Dictionary or results with values of true or false
    :return: Dict of messages, key's are the appropriate flash category. False on error.
    """
    if not isinstance(results, dict):
        return False
    
    for key, val in results.items():
        if key == None or key == "":
            return False
        if not isinstance(key, str) or not isinstance(val, bool):
            return False

    success_fields = [field for field, ok in results.items() if ok]
    fail_fields = [field for field, ok in results.items() if not ok]

    messages = {}
    if success_fields:
        success_msg = "Successfully deleted: " + ", ".join(success_fields) + "."
        messages["warning"] = success_msg
    if fail_fields:
        failure_msg = "Failed to delete: " + ", ".join(fail_fields) + "."
        messages["danger"] = failure_msg

    return messages

def flash_status_messages(messages: dict):
    """
    Flashes the supplied messages appropriately by category.

    :param messages: Dict of the messages, key should be the category, val the message.
    :return: True for success, false for failure.    
    """
    try:
        if messages and isinstance(messages, dict):
            for key, val in messages.items():
                if len(key) > 0 and len(val) > 0:
                    flash(val, key)
                else:
                    return False
            return True
        else:
            return False
    except (ValueError, TypeError):
        print("Error flashing messages.")
        return False

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