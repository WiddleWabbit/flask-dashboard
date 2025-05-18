# Import the required libraries
import os
from flask import Flask, request, render_template, url_for, redirect
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

# User model
class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)
    firstname = db.Column(db.String(250), nullable=False)
    lastname = db.Column(db.String(250), nullable=False)
    email = db.Column(db.String(250), unique=True, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True),server_default=func.now())

    def __repr__(self):
        return f'<User {self.firstname}>'

# Create database
# create all does not overwrite or recreate existing
with app.app_context():
    db.create_all()

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
            return render_template("login.html", error="Invalid username or password")

    return render_template("login.html")

# Account Route
@app.route("/account", methods=["GET", "POST"])
def account():
    return render_template("account.html")

# Logout Route
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))