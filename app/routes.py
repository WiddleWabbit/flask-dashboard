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
from .func import *

bp = Blueprint('routes', __name__)

# Homepage Test Route
@bp.route("/")
def home():
    return render_template('dashboard.html')

# Dashboard Route
@bp.route("/dashboard")
@login_required
def dashboard():
    return render_template('dashboard.html')

# Configuration Route
@bp.route("/configuration", methods=["GET", "POST"])
def configuration():

    if request.method == "POST":

        if not current_user.is_authenticated:
            flash('You need to login to make modifications.', 'danger')
            return redirect(url_for("routes.schedules"))
        
        lat = sanitise(request.form.get("latitude"), float)
        long = sanitise(request.form.get("longitude"),float)
        if not lat and not long:
            flash('Nothing input for latitude or longitude.', 'danger')
            return redirect(url_for("routes.schedules"))
        if lat:
            set_setting("latitude", lat)
        if long:
            set_setting("longitude", long)

        flash("You've successfully updated the coordinates", 'success')
        return redirect(url_for("routes.configuration"))

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
@bp.route("/zones", methods=["GET", "POST"])
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
                return redirect(url_for("routes.zones"))

            else:
                
                flash('Empty form submitted', 'danger')
                return redirect(url_for("routes.zones"))

    

    zones = get_all_zones()
    if not zones:
        zones = [{"id":1, "name":"", "description":"", "solenoid":""}]
    
    return render_template('zones.html', zones=zones)

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

# Login Route
@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":

        username = sanitise(request.form.get("username"))
        password = sanitise(request.form.get("password"))

        user = get_user(username)

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("routes.dashboard"))
        else:
            flash('Invalid username or password', 'danger')
            return render_template("login.html", error="Invalid username or password")

    return render_template("login.html")

# Account Route
@bp.route("/account", methods=["GET", "POST"])
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
                return redirect(url_for("routes.account"))

            if check_password_hash(user.password, current_password):
                hashed_password = generate_password_hash(new_password, method="pbkdf2:sha256")
                update_user(user.username, "password", hashed_password)
                flash("You've successfully updated your password.", 'success')
                return redirect(url_for("routes.account"))
            else:
                flash('Provided new passwords do not match!', 'danger')
                return redirect(url_for("routes.account"))

        elif request.args.get("form") == "update_details":
            current_password = sanitise(request.form.get("current_password_details"))
            username = sanitise(request.form.get("username"))
            firstname = sanitise(request.form.get("firstname"))
            lastname = sanitise(request.form.get("lastname"))
            email = sanitise(request.form.get("email"))

            if check_password_hash(user.password, current_password):
                if not username and not firstname and not lastname and not email:
                    flash("No fields submitted to change.", 'danger')
                    return redirect(url_for("routes.account"))
                if username:
                    if get_user(username):
                        flash('Unable to update. Username already exists.', 'danger')
                        return redirect(url_for("routes.account"))
                    update_user(user.username, "username", username)
                if firstname:
                    update_user(user.username, "firstname", firstname)
                if lastname:
                    update_user(user.username, "lastname", lastname)
                if email:
                    update_user(user.username, "email", email)

                flash("You've successfully updated your details.", 'success')
                return redirect(url_for("routes.account"))
            else:
                flash('Password entered is incorrect!', 'danger')
                return redirect(url_for("routes.account"))
    return render_template("account.html", user = user, created = formatted_created)

# Logout Route
@bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("routes.home"))