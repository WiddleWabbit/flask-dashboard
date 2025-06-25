from ..models import db
from flask_login import UserMixin
from datetime import datetime, time
import pytz

# Association table for many-to-many relationship between Zones and Schedules
zone_schedules = db.Table(
    'zone_schedules',
    db.Column('zone_id', db.Integer, db.ForeignKey('zones.id'), primary_key=True),
    db.Column('schedule_id', db.Integer, db.ForeignKey('schedules.id'), primary_key=True)
)

# Association table for many-to-many relationship between Schedules and DaysOfWeek
schedule_days = db.Table(
    'schedule_days',
    db.Column('schedule_id', db.Integer, db.ForeignKey('schedules.id'), primary_key=True),
    db.Column('day_id', db.Integer, db.ForeignKey('days_of_week.id'), primary_key=True)
)

# DaysOfWeek Database Model
class DaysOfWeek(db.Model):
    __tablename__ = "days_of_week"
    id = db.Column(db.Integer, primary_key=True, unique=True)
    name = db.Column(db.String(20), unique=True, nullable=False)

    def __repr__(self):
        return f'<{self.name}>'

# Schedule Groups Database Model
class Groups(db.Model):
    __tablename__ = "groups"
    id = db.Column(db.Integer, primary_key=True, unique=True)
    name = db.Column(db.String(100), unique=False)
    schedules = db.relationship(
        'Schedules',
        lazy=True,
        backref=db.backref('groups', lazy=True),
        cascade="all, delete"
    )

    def __repr__(self):
        return f'<{self.name}>'


# Zones Database Model
class Zones(db.Model):
    __tablename__ = "zones"
    __table_args__ = {'sqlite_autoincrement': True}
    id = db.Column(db.Integer, primary_key=True, unique=True, autoincrement=True)
    name = db.Column(db.String(250), nullable=False)
    description = db.Column(db.String(250), nullable=True)
    solenoid = db.Column(db.Integer, nullable=False, unique=True)
    created_at = db.Column(db.String(60), nullable=False, default=datetime.now(pytz.utc))
    schedules = db.relationship(
        'Schedules',
        secondary=zone_schedules,
        lazy='subquery',
        backref=db.backref('zones', lazy='subquery'),
        cascade="all, delete"
    )

    def __repr__(self):
        return f'<{self.name}>'

# Schedules Database Model
# Auto increment on for the ID to prevent ID's being reused after one is removed.
class Schedules(db.Model):
    __tablename__ = "schedules"
    __table_args__ = {'sqlite_autoincrement': True}
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    group = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
    sort_order = db.Column(db.Integer, nullable=True)
    start = db.Column(db.String(50), nullable=False)
    end = db.Column(db.String(50), nullable=False)
    active = db.Column(db.Integer, nullable=False)
    weather_dependent = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.String(60), nullable=False, default=datetime.now(pytz.utc))
    days = db.relationship(
        'DaysOfWeek', 
        secondary=schedule_days,
        lazy=True,
        backref=db.backref('schedules', lazy=True))

    def __repr__(self):
        return f'<{self.id}>'