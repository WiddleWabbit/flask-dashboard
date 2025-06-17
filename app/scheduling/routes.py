# Import the required libraries
from datetime import datetime, time
from flask import Blueprint, Flask, request, render_template, url_for, redirect, flash
from flask_login import current_user
from sqlalchemy import func
from .models import db, Groups, Schedules, Zones, DaysOfWeek, schedule_days, zone_schedules
from ..func import sanitise, update_status_messages, flash_status_messages, delete_status_messages, to_isotime
#from .. import db
import re
from .func import *

bp = Blueprint('scheduling_routes', __name__)

# Return the variables to build the configuration page.
def config_zones():
    data = {}
    data['zones'] = get_all_zones()
    if not data['zones']:
        data['zones'] = [{"id":1, "name":"", "description":"", "solenoid":""}]
    return data

# Zones Route
@bp.route("/zones", methods=["GET", "POST"])
def zones():

    if request.method == "GET":
        
        return render_template('zones.html', data=config_zones())

    if request.method == "POST":

        if request.args.get("form") == "update_zones":
            
            # Check authenticated
            if not current_user.is_authenticated:
                flash('You need to login to make modifications.', 'danger')
                return render_template('zones.html', data=config_zones()), 403

            fields = request.form.items()
            if fields:

                # Process the fields
                #fields = request.form.items()
                num_zones = count_fields(fields)
                update_results = {}
                delete_results = {}

                # Update submitted zones
                for i in range(1, num_zones + 1):

                    id = sanitise(request.form.get(f"id-{i}"))
                    name = sanitise(request.form.get(f"name-{i}"))
                    desc = sanitise(request.form.get(f"description-{i}"))
                    solenoid = sanitise(request.form.get(f"solenoid-{i}"))

                    # Ensure that the required fields were submitted
                    if not id or not name or not solenoid:
                        update_results[f'Zone {id} "{name}"'] = False

                    else:
                        # If the description field fails (usually because it's blank), just make it blank.
                        if not desc:
                            desc = ""
                        # Update the zone
                        update_results[f'Zone {id} "{name}"'] = update_zone(id, name, desc, solenoid)

                # Check for unsubmitted zones and delete
                all_zones = get_all_zones()
                if all_zones:
                    if len(all_zones) > num_zones:

                        # Starting from zone following last zone submitted
                        next_zone_id = num_zones + 1
                        while next_zone_id <= len(all_zones):

                            # Delete the removed zones
                            delete_results[f'Zone {id} "{name}"'] = delete_zone(next_zone_id)
                            next_zone_id = next_zone_id + 1

                # Flash the messages of the updates and deletes
                update_messages = update_status_messages(update_results)
                flash_status_messages(update_messages)
                delete_messages = delete_status_messages(delete_results)
                flash_status_messages(delete_messages)
                return redirect(url_for("scheduling_routes.zones"))

            else:
                
                flash('Empty form submitted', 'danger')
                return redirect(url_for("scheduling_routes.zones"))

# Return the variables to build the configuration page.
def config_schedules():

    data = {}
    data['groups'] = get_all_groups()
    data['zones'] = get_all_zones()
    data['days_of_week'] = DaysOfWeek.query.all()
    data['max_schedule_id'] = db.session.query(func.max(Schedules.id)).scalar() or 0

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

    data['schedule_durations'] = schedule_durations

    # if not data['zones']:
    #     data['zones'] = [{"id":1, "name":"", "description":"", "solenoid":""}]
    return data

# Schedules Route
@bp.route("/schedules", methods=["GET", "POST"])
def schedules():

    if request.method == "GET":

        return render_template('schedules.html', data=config_schedules())

    if request.method == "POST":

        if request.args.get("form") == "update_schedules":

            # Check authenticated
            if not current_user.is_authenticated:
                flash('You need to login to make modifications.', 'danger')
                return render_template('schedules.html', data=config_schedules()), 403

            # Fetch the fields and process
            fields = request.form.items()
            if fields:

                # Count the fields and other data from database that is required
                ######## We will want a count schedules function #######
                num_schedules = count_fields(fields)
                days = DaysOfWeek.query.all()
                zones = get_all_zones()

                # Error checking these fields error if unexpected value
                if not num_schedules or not days or not zones or num_schedules < 1 or len(days) < 1 or len(zones) < 1:
                    flash('Serious error, please try again or contact your system administrator.', 'danger')
                    return render_template('schedules.html', data=config_schedules()), 422

                update_results = {}
                delete_results = {}
                sanitised_fields = {}

                # Store groups
                groups_submitted = {}
                groups_submitted = {key: request.form[key] for key in request.form if re.match(r'^group-name-\d+$', key)}
                print(f'Groups submitted: {groups_submitted}')
                # Validate groups
                for key, val in groups_submitted.items():
                    if not isinstance(key, str) or not isinstance(val, str):
                        print(f'Group names or values are not valid {key}: {val}')
                        flash('Group names or values are not valid. Error in submission. No values saved.', 'danger')
                        return render_template('schedules.html', data=config_schedules()), 422

                # Iterate through the fields submitted
                for i in range(1, num_schedules + 1):

                    print(f'Processing schedule {i}')

                    # Sanitse all the fields submitted
                    sanitised_fields['start'] = sanitise(request.form.get(f"start-{i}"))
                    sanitised_fields['duration'] = sanitise(request.form.get(f"duration-{i}"), int)
                    sanitised_fields['weather'] = sanitise(request.form.get(f"weather-{i}"), int)
                    sanitised_fields['active'] = sanitise(request.form.get(f"active-{i}"))
                    sanitised_fields['group'] = sanitise(request.form.get(f"group-{i}"))



                    sanitised_fields['id'] = sanitise(request.form.get(f"id-{i}"))
                    sanitised_fields['sort-order'] = sanitise(request.form.get(f"sort-order-{i}"))



                    sanitised_fields['days'] = {}
                    for day in days:
                        sanitised_fields['days'][f'{day.id}'] = sanitise(request.form.get(f"day-{day.id}-schedule-{i}"))
                    sanitised_fields['zones'] = {}
                    for zone in zones:
                        sanitised_fields['zones'][f'{zone.id}'] = sanitise(request.form.get(f"zone-{zone.id}-schedule-{i}"))
                    
                    print(sanitised_fields)

                    # Validate form fields
                    if not sanitised_fields['start'] or not datetime.strptime(sanitised_fields['start'], "%H:%M"):
                        print(f'Start not valid {sanitised_fields["start"]}')
                        update_results[f'schedule-{i}'] = False
                        break
                    if not sanitised_fields['duration'] or not isinstance(sanitised_fields['duration'], int):
                        print(f'duration not valid {sanitised_fields["duration"]}')
                        update_results[f'schedule-{i}'] = False
                        break
                    if not sanitised_fields['weather'] or sanitised_fields['weather'] > 3:
                        print(f'weather not valid {sanitised_fields["weather"]}')
                        update_results[f'schedule-{i}'] = False
                        break
                    if not sanitised_fields['group'] or not isinstance(int(sanitised_fields['group'].split('-')[1]), int):
                        print(f'group not valid {sanitised_fields["group"]}')
                        update_results[f'schedule-{i}'] = False
                        break
                    if not sanitised_fields['active'] in {'on', False}:
                        print(f'active not valid {sanitised_fields["active"]}')
                        update_results[f'schedule-{i}'] = False
                        break
                    for key, val in sanitised_fields['days'].items():
                        if val not in {'on', False}:
                            print(f'day not valid {key}: {val}')
                            update_results[f'schedule-{i}'] = False
                            break
                    for key, val in sanitised_fields['zones'].items():
                        if val not in {'on', False}:
                            print(f'zone not valid {key}: {val}')
                            update_results[f'schedule-{i}'] = False
                            break
                    
                    # Reformat fields for schedule update
                    field_updates = {}
                    field_updates['start'] = sanitised_fields['start']
                    field_updates['end'] = add_minutes_to_time(field_updates['start'], sanitised_fields['duration'])
                    field_updates['weather_dependent'] = sanitised_fields['weather']
                    field_updates['group'] = int(sanitised_fields['group'].split('-')[1])
                    if not field_updates['group']:
                        print(f'Unable to fetch group {sanitised_fields["group"]}')
                        update_results[f'schedule-{i}'] = False
                        break
                    field_updates['active'] = 1 if sanitised_fields['active'] == 'on' else 0
                    field_updates['days'] = []
                    for key, val in sanitised_fields['days'].items():
                        if val == 'on':
                            day = get_day(int(key))
                            if day:
                                field_updates['days'].append(day)
                            else:
                                print(f'Unable to fetch day {key}')
                                update_results[f'schedule-{i}'] = False
                                break
                    field_updates['zones'] = []
                    for key, val in sanitised_fields['zones'].items():
                        if val == 'on':
                            zone = get_zone(int(key))
                            if zone:
                                field_updates['zones'].append(zone)
                            else:
                                print(f'Unable to fetch zone {key}')
                                update_results[f'schedule-{i}'] = False
                                break

                    print(field_updates)

                    # Create this schedules group if it doesn't exist
                    group_id = sanitised_fields['group'].split('-')[1]
                    update_results[f'Group: {group_id}'] = update_group(int(group_id), groups_submitted[f"group-name-{group_id}"])

                    # Update schedules
                    update_results[f'schedule-{i}'] = update_schedule(i, field_updates['group'], field_updates['start'], field_updates['end'], field_updates['active'], field_updates['weather_dependent'], field_updates['days'], field_updates['zones'])
                    
                # Delete additional groups and all associated schedules
                all_groups = get_all_groups()
                if all_groups:
                    if len(all_groups) > len(groups_submitted):
                        del_group_id = len(groups_submitted) + 1
                        while del_group_id <= len(all_groups):
                            # Grab the group's name so we can print a readable message
                            group_name = get_group(del_group_id).name
                            # Delete the removed zones - schedules are deleted automatically due to the cascade deletion on the model
                            delete_results[f'Group: {group_name}'] = delete_group(del_group_id)
                            del_group_id = del_group_id + 1
                else:
                    flash('Failed to delete any groups', 'danger')

                # Identify and delete schedules that were deleted as well
                all_schedules = get_all_schedules()
                if all_schedules:
                    if len(all_schedules) > num_schedules:
                        del_schedule_id = num_schedules + 1
                        while del_schedule_id <= len(all_schedules):
                            # Delete the removed schedules
                            delete_results[f'Schedule: {del_schedule_id}'] = delete_schedule(del_schedule_id)
                            del_schedule_id = del_schedule_id + 1
                else:
                    flash('Failed to delete schedules removed from groups.', 'danger')

            else:
                flash('No fields submitted, please try again.', 'danger')
                return render_template('schedules.html', data=config_schedules()), 422

            # Redirect and print messages to screen
            update_messages = update_status_messages(update_results)
            flash_status_messages(update_messages)
            delete_messages = delete_status_messages(delete_results)
            flash_status_messages(delete_messages)
            return redirect(url_for("scheduling_routes.schedules"))