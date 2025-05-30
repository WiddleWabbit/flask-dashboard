from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
import pytz

# Notes
#from datetime import datetime, time
#datetime.now(pytz.utc)

# Create the SQL Alchemy Object
db = SQLAlchemy()

# User Database Model
class Users(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)
    firstname = db.Column(db.String(250), nullable=False)
    lastname = db.Column(db.String(250), nullable=False)
    email = db.Column(db.String(250), unique=True, nullable=False)
    created_at = db.Column(db.String(60), nullable=False, default=func.now(pytz.utc))

    def __repr__(self):
        return f'<{self.username}>'

# Settings Database Model
class Settings(db.Model):
    __tablename__ = "settings"
    id = db.Column(db.Integer, primary_key=True, unique=True)
    setting = db.Column(db.String(250), unique=True, nullable=False)
    value = db.Column(db.String(250), unique=False, nullable=False)

    def __repr__(self):
        return f'<{self.setting}>'