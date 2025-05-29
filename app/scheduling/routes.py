# Import the required libraries
from datetime import datetime, time
from flask import Blueprint, Flask, request, render_template, url_for, redirect, flash
#from flask_login import login_user, logout_user, login_required, current_user
#from apscheduler.schedulers.background import BackgroundScheduler
#from apscheduler.triggers.cron import CronTrigger
from .models import Groups, Schedules, Zones, DaysOfWeek, schedule_days, zone_schedules
from .. import db
from ..func import sanitise
from .func import *

bp = Blueprint('scheduling_routes', __name__)

# Zones Route
@bp.route("/zones", methods=["GET", "POST"])
def zones():

    if request.method == "POST":

        if request.args.get("form") == "update_zones":
            
            #submission = {}
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
                num_zones = len(numbers)

                # Update submitted zones
                for i in range(1, num_zones + 1):

                    id = sanitise(request.form.get(f"id-{i}"))
                    name = sanitise(request.form.get(f"name-{i}"))
                    desc = sanitise(request.form.get(f"description-{i}"))
                    solenoid = sanitise(request.form.get(f"solenoid-{i}"))

                    update_zone(id, name, desc, solenoid)

                # Check for unsubmitted zones and delete
                all_zones = get_all_zones()
                if all_zones:
                    if len(all_zones) > num_zones:

                        # Starting from zone following last zone submitted
                        next_zone_id = num_zones + 1
                        while next_zone_id <= len(all_zones):

                            delete_zone(next_zone_id)
                            next_zone_id = next_zone_id + 1

                flash("Successfully updated zones.", 'success')
                return redirect(url_for("scheduling_routes.zones"))

            else:
                
                flash('Empty form submitted', 'danger')
                return redirect(url_for("scheduling_routes.zones"))

    

    all_zones = get_all_zones()
    if not all_zones:
        zones = [{"id":1, "name":"", "description":"", "solenoid":""}]
    
    return render_template('zones.html', zones=all_zones)

# Schedules Route
@bp.route("/schedules", methods=["GET", "POST"])
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
