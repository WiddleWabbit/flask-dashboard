# Import the required libraries
import os
from datetime import datetime, time
import pytz
from flask import Flask, request, render_template, url_for, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# Create the application
app = Flask(__name__)

# Setup DB Configuration
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "aXZ!#fl2IlR4ka6n**f6D7e8*F92#D4nf"

# Initialise SQL Alchemy and Login Manager
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# User Database Model
class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)
    firstname = db.Column(db.String(250), nullable=False)
    lastname = db.Column(db.String(250), nullable=False)
    email = db.Column(db.String(250), unique=True, nullable=False)
    created_at = db.Column(db.String(60), nullable=False, default=datetime.now(pytz.utc))
    #created_at = db.Column(db.DateTime(timezone=True),server_default=func.now())

    def __repr__(self):
        return f'<User {self.username}>'

# Settings Database Model
class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    setting = db.Column(db.String(250), unique=True, nullable=False)
    value = db.Column(db.String(250), unique=False, nullable=False)

    def __repr__(self):
        return f'<Setting {self.setting}'

# Prepare the application
with app.app_context():

    # Create the database, does not create or override already existing
    db.create_all()
    
    # Create a default user if none exist
    user_exists = Users.query.first()
    if not user_exists:
        password = "admin"
        hashed_password=generate_password_hash(password,method="pbkdf2:sha256")
        admin_user = Users(username="admin",password=hashed_password,firstname="Admin",lastname="User",email="test@test.com")
        db.session.add(admin_user)
        db.session.commit()

    # Create the timezone setting if it doesn't exist
    timezone = Settings.query.filter_by(setting="timezone").first()
    if not timezone:
        timezone = 'Australia/Perth'
        db.session.add(Settings(setting="timezone",value=timezone))
    
    # Create the sunrise and sunset settings if they don't exist
    sunrise_exists = Settings.query.filter_by(setting="sunrise_iso").first()
    sunset_exists = Settings.query.filter_by(setting="sunset_iso").first()
    if not sunrise_exists:
        now = datetime.now(pytz.timezone(timezone))
        sixam_naive = datetime.combine(now.date(), time(6, 0, 0))
        sixam_perth = pytz.timezone(timezone).localize(sixam_naive)
        sixam_utc = sixam_perth.astimezone(pytz.utc)
        sunrise_iso = sixam_utc.isoformat()
        db.session.add(Settings(setting="sunrise_iso", value=sunrise_iso))
        db.session.commit()
    if not sunset_exists:
        now = datetime.now(pytz.timezone(timezone))
        sixpm_naive = datetime.combine(now.date(), time(18, 0, 0))
        sixpm_perth = pytz.timezone(timezone).localize(sixpm_naive)
        sixpm_utc = sixpm_perth.astimezone(pytz.utc)
        sunset_iso = sixpm_utc.isoformat()
        db.session.add(Settings(setting="sunset_iso", value=sunset_iso))
        db.session.commit()

# Define the user loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))


# Homepage Test Route
@app.route("/")
def home():
    return render_template('dashboard.html')

# Dashboard Route
@app.route("/dashboard")
@login_required
def dashboard():
    return render_template('dashboard.html')

# Schedules Route
@app.route("/schedules", methods=["GET", "POST"])
def schedules():

    timezone = Settings.query.filter_by(setting="timezone").first()

    sunrise = Settings.query.filter_by(setting="sunrise_iso").first()
    sunrise_iso = datetime.fromisoformat(sunrise.value)
    sunrise_time = sunrise_iso.astimezone(pytz.timezone('Australia/Perth')).strftime("%I:%M%p")

    sunset = Settings.query.filter_by(setting="sunset_iso").first()
    sunset_iso = datetime.fromisoformat(sunset.value)
    sunset_time = sunset_iso.astimezone(pytz.timezone('Australia/Perth')).strftime("%I:%M%p")

    return render_template('schedules.html', timezone = timezone, sunrise = sunrise_time, sunset = sunset_time)

# Login Route
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # Read Form
        username = request.form.get("username")
        password = request.form.get("password")
        # Get the relevant user
        user = Users.query.filter_by(username=username).first()
        # See if the password matches
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("dashboard"))
        else:
            flash('Invalid username or password', 'danger')
            return render_template("login.html", error="Invalid username or password")

    return render_template("login.html")

# Account Route
@app.route("/account", methods=["GET", "POST"])
@login_required
def account():
    user = Users.query.filter_by(username=current_user.username).first()
    created_at = datetime.fromisoformat(user.created_at)
    created_tzc = created_at.astimezone(pytz.timezone('Australia/Perth'))
    formatted_created = created_tzc.strftime('%B %d, %Y, %I:%M %p')
    user_details = {'username':user.username, 'firstname': user.firstname, 'lastname': user.lastname, 'email':user.email, 'created':formatted_created}
    if request.method == "POST":
        # Change password form
        if request.args.get("form") == "change_password":
            current_password = request.form.get("current_password")
            new_password = request.form.get("new_password")
            new_password_conf = request.form.get("new_password_conf")
            # Check new passwords match
            if new_password != new_password_conf:
                flash('Provided new passwords do not match!', 'danger')
                return redirect(url_for("account"))
            # Confirm password is correct
            if check_password_hash(user.password, current_password):
                hashed_password = generate_password_hash(new_password, method="pbkdf2:sha256")
                user.password = hashed_password
                db.session.commit()
                flash("You've successfully updated your password.", 'success')
                return redirect(url_for("account"))
            else:
                flash('Provided new passwords do not match!', 'danger')
                return redirect(url_for("account"))
        # Update user details form
        elif request.args.get("form") == "update_details":
            current_password = request.form.get("current_password_details")
            username = request.form.get("username")
            firstname = request.form.get("firstname")
            lastname = request.form.get("lastname")
            email = request.form.get("email")
            # Confirm password correct
            if check_password_hash(user.password, current_password):
                if not username and not firstname and not lastname and not email:
                    flash("No fields submitted to change.", 'danger')
                    return redirect(url_for("account"))
                if username:
                    new_username = Users.query.filter_by(username=username).first()
                    if new_username:
                        flash('Unable to update. Username already exists.', 'danger')
                        return redirect(url_for("account"))
                    user.username = username
                if firstname:
                    user.firstname = firstname
                if lastname:
                    user.lastname = lastname
                if email:
                    user.email = email
                db.session.commit()
                flash("You've successfully updated your details.", 'success')
                return redirect(url_for("account"))
            else:
                flash('Password entered is incorrect!', 'danger')
                return redirect(url_for("account"))
    return render_template("account.html", user = user_details)

# Logout Route
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))