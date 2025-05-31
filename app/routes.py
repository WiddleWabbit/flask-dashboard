# Import the required libraries
from flask import Blueprint, Flask, request, render_template, url_for, redirect, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from .func import *

bp = Blueprint('routes', __name__)

# Homepage Test Route
@bp.route("/")
def home():
    return render_template('dashboard.html')

# Dashboard Route
@bp.route("/dashboard")
def dashboard():
    return render_template('dashboard.html')

# Configuration Route
@bp.route("/configuration", methods=["GET", "POST"])
def configuration():

    if request.method == "POST":

        if not current_user.is_authenticated:
            flash('You need to login to make modifications.', 'danger')
            return redirect(url_for("routes.configuration"))
        
        lat = sanitise(request.form.get("latitude"), float)
        long = sanitise(request.form.get("longitude"),float)
        if not lat and not long:
            flash('Nothing input for latitude or longitude.', 'danger')
            return redirect(url_for("routes.configuration"))
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