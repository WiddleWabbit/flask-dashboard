# Import the required libraries
from datetime import datetime, time
from flask import Blueprint, Flask, request, render_template, url_for, redirect, flash
from flask_login import current_user
from .models import db, Groups, Schedules, Zones, DaysOfWeek, schedule_days, zone_schedules
from ..func import sanitise, update_status_messages, flash_status_messages, delete_status_messages
#from .. import db
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
                fields = request.form.items()
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

        # groups = get_all_groups()
        # zones = get_all_zones()
        # days_of_week = DaysOfWeek.query.all()

        # # Create a dict of schedule durations by schedule id
        # schedule_durations = {}
        # all_schedules = Schedules.query.all()
        # for sched in all_schedules:
        #     try:
        #         start_dt = datetime.strptime(sched.start, "%H:%M")
        #         end_dt = datetime.strptime(sched.end, "%H:%M")
        #         # Handle overnight schedules
        #         if end_dt < start_dt:
        #             end_dt = end_dt.replace(day=start_dt.day + 1)
        #         duration = (end_dt - start_dt).seconds // 60
        #         schedule_durations[sched.id] = duration
        #     except Exception as e:
        #         schedule_durations[sched.id] = None

        #return render_template('schedules.html', groups=groups, days=days_of_week, zones=zones, schedule_durations=schedule_durations)
        return render_template('schedules.html', data=config_schedules())

    if request.method == "POST":

        if request.args.get("form") == "update_zones":

            return redirect(url_for("scheduling_routes.schedules"))