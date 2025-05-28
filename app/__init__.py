# Import the required libraries
import os
import html
from datetime import datetime, time
import pytz
from flask import Flask, request, render_template, url_for, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import requests

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_object('app.config.Config')

    #db = SQLAlchemy(app)
    db.init_app(app)
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "routes.login"

    from .models import Users
    @login_manager.user_loader
    def load_user(user_id):
        return Users.query.get(int(user_id))

    from .routes import bp as routes_bp
    app.register_blueprint(routes_bp)

    return app