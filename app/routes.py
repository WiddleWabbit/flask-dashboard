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

# Return the variables to build the configuration page.
def config_data():

    data = {}
    data["mqtt_user"] = get_setting("mqtt_user")
    data["watering_topic"] = get_setting("watering_topic")
    data["sensor_topic"] = get_setting("sensor_topic")
    data["timezone"] = get_setting("timezone")
    data["latitude"] = get_setting("latitude")
    data["longitude"] = get_setting("longitude")
    data["times"] = {
        "sunrise": format_isotime(get_setting("sunrise_iso")),
        "sunset": format_isotime(get_setting("sunset_iso")),
        "dawn": format_isotime(get_setting("dawn_iso")),
        "dusk": format_isotime(get_setting("dusk_iso")),
        "first_light": format_isotime(get_setting("first_light_iso")),
        "last_light": format_isotime(get_setting("last_light_iso"))
    }
    return data

# Configuration Route
@bp.route("/configuration", methods=["GET", "POST"])
def configuration():

    if request.method == "GET":

        return render_template('configuration.html', data = config_data()), 200
    
    if request.method == "POST":

        if request.args.get("form") == "mqtt_settings":
            # Check authenticated
            if not current_user.is_authenticated:
                flash('You need to login to make modifications.', 'danger')
                return render_template('configuration.html', data = config_data()), 403
            # Validate form
            user = sanitise(request.form.get("mqtt_user"))
            password = sanitise(request.form.get("mqtt_password"))
            watering_topic = sanitise(request.form.get("watering_topic"))
            sensor_topic = sanitise(request.form.get("sensor_topic"))
            if not user:
                flash('Please ensure a MQTT user is set.', 'danger')
                return render_template('configuration.html', data = config_data()), 422
            if not get_setting("mqtt_password"):
                if not password:
                    flash('Please input a valid password for mqtt user.', 'danger')
                    return render_template('configuration.html', data = config_data()), 422
            if not watering_topic or not sensor_topic:
                flash('Please input sensor and watering topics.', 'danger')
                return render_template('configuration.html', data = config_data()), 422
            
            # Update the settings
            results = {}
            results["MQTT User"] = set_setting("mqtt_user", user)
            if password:
                hashed_password = generate_password_hash(password, method="pbkdf2:sha256")
                results["MQTT Password"] = set_setting("mqtt_password", hashed_password)
            results["Watering Topic"] = set_setting("watering_topic", watering_topic)
            results["Sensor Topic"] = set_setting("sensor_topic", sensor_topic)

            # Redirect back to page
            messages = update_status_messages(results)
            flash_status_messages(messages)
            return redirect(url_for("routes.configuration"))

        # Time settings form submitted
        if request.args.get("form") == "time_settings":
            # Check authenticated
            if not current_user.is_authenticated:
                flash('You need to login to make modifications.', 'danger')
                return render_template('configuration.html', data = config_data()), 403
            # Check something submitted.
            if not request.form.get("latitude") and not request.form.get("longitude"):
                flash('Nothing valid input for latitude or longitude.', 'danger')
                return render_template('configuration.html', data = config_data()), 422
            # Process the form
            results = {}
            lat = sanitise(request.form.get("latitude"), float)
            if lat:
                lat = str(lat)
                results["latitude"] = set_setting("latitude", lat)
            long = sanitise(request.form.get("longitude"), float)
            if long:
                long = str(long)
                results["longitude"] = set_setting("longitude", long)
            messages = update_status_messages(results)
            flash_status_messages(messages)
            return redirect(url_for("routes.configuration"))
        
        # Not a valid url argument, redirect
        else:
            return redirect(url_for("routes.configuration"))

# Login Route
@bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "GET":
            
        return render_template("login.html"), 200

    if request.method == "POST":

        # Login form submitted
        if request.args.get("form") == "login":

            # Check authenticated
            if current_user.is_authenticated:
                flash('You are already logged in', 'warning')
                return redirect(url_for("routes.dashboard"))

            username = sanitise(request.form.get("username"))
            password = sanitise(request.form.get("password"))

            # Confirm both a username and password were submitted
            if not username or not password:
                flash('Please submit a username and a password.', 'danger')
                return render_template("login.html"), 403

            user = get_user(username)

            # Attempt login
            if user and check_password_hash(user.password, password):
                login_user(user)
                success_msg = "Welcome back " + user.firstname
                flash(success_msg, 'success')
                return redirect(url_for("routes.dashboard"))
            else:
                flash('Invalid username or password', 'danger')
                return render_template("login.html"), 403
        
        # Not a valid url argument, redirect
        else:
            return redirect(url_for("routes.login"))

# Return the variables to build the account page.
def account_data():
    data = {}
    data["user"] = get_user(username=current_user.username)
    data["formatted_created"] = format_isotime(data["user"].created_at, "%B %d, %Y, %I:%M %p")
    return data

# Account Route
@bp.route("/account", methods=["GET", "POST"])
@login_required
def account():

    # Get Request
    if request.method == "GET":

        return render_template("account.html", data=account_data()), 200
    
    # Post Request
    elif request.method == "POST":

        user = get_user(username=current_user.username)

        # Change Password Form
        if request.args.get("form") == "change_password":

            current_password = sanitise(request.form.get("current_password"))
            new_password = sanitise(request.form.get("new_password"))
            new_password_conf = sanitise(request.form.get("new_password_conf"))

            # Validate all forms had valid inputs
            if not current_password or not new_password or not new_password_conf:
                flash('Please submit your current password, new password and confirmation of your new password.', 'danger')
                return render_template("account.html", data=account_data()), 403

            # Confirm that the new password confirmation mathes the new password
            if new_password != new_password_conf:
                flash('Provided new passwords do not match.', 'danger')
                return render_template("account.html", data=account_data()), 403

            # Confirm the current password is correct, if so update the password
            if check_password_hash(user.password, current_password):
                hashed_password = generate_password_hash(new_password, method="pbkdf2:sha256")
                if update_user(user.username, "password", hashed_password):
                    flash("You've successfully updated your password.", 'success')
                    return redirect(url_for("routes.account"))
                else:
                    flash('Something went wrong. Please try again.', 'danger')
                    return redirect(url_for("routes.account"))
            else:
                flash('Incorrect password entered.', 'danger')
                return redirect(url_for("routes.account"))

        # Update account details form
        elif request.args.get("form") == "update_details":

            current_password = sanitise(request.form.get("current_password_details"))
            username = sanitise(request.form.get("username"))
            firstname = sanitise(request.form.get("firstname"))
            lastname = sanitise(request.form.get("lastname"))
            email = sanitise(request.form.get("email"))

            # Validate the password was sanitised correctly.
            if not current_password:
                flash('Please input your current password along with changes.', 'danger')
                return render_template("account.html", data=account_data()), 403

            # Validate the password is correct
            if not check_password_hash(user.password, current_password):
                flash('Password entered is incorrect.', 'danger')
                return render_template("account.html", data=account_data()), 403

            # Confirm at least one field was submitted
            if not username and not firstname and not lastname and not email:
                flash("No fields submitted to change.", 'danger')
                return render_template("account.html", data=account_data()), 422
            
            # Validate the username or email being changed is unique.
            if username or email:
                if username:
                    if get_user(username):
                        flash('Unable to update. Username already exists.', 'danger')
                        return render_template("account.html", data=account_data()), 422
                elif email:
                    if len(Users.query.filter_by(email=email).all()) > 0:
                        flash('Unable to update. Email already exists.', 'danger')
                        return render_template("account.html", data=account_data()), 422
                else:
                    flash('Something went wrong. Please try again.', 'danger')
                    return render_template("account.html", data=account_data()), 400

            results = {}

            # Update the fields input
            if username:
                results['username'] = update_user(user.username, "username", username)
            if firstname:
                results['firstname'] = update_user(user.username, "firstname", firstname)
            if lastname:
                results['lastname'] = update_user(user.username, "lastname", lastname)
            if email:
                results['email'] = update_user(user.username, "email", email)

            messages = update_status_messages(results)
            flash_status_messages(messages)
            return redirect(url_for("routes.account"))       
    
    # Not a valid form / post request, redirect
    else:
        return redirect(url_for("routes.account"))

# Logout Route
@bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("routes.home"))