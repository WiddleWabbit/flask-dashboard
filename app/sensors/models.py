from flask_sqlalchemy import SQLAlchemy
from app.models import db

# Calibration Table, store calibration data.
# When calibration disabled, average out and create offset.

class Sensors(db.Model):
    __tablename__ = "sensors"
    __table_args__ = (
        db.Index('idx_depth_sensor_timestamp', 'identifier'),
    )
    id = db.Column(db.Integer, primary_key=True, unique=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    identifier = db.Column(db.String, nullable=False, unique=True)
    calibration = db.Column(db.Float, nullable=False)
    type = db.Column(db.String, nullable=False)
    calibration_mode = db.Column(db.Integer, nullable=False)
    sort_order = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f'<{self.name}>'

class WaterDepth(db.Model):
    __tablename__ = "waterdepth"
    __table_args__ = (
        db.Index('idx_depth_sensor_timestamp', 'sensor_id', 'timestamp'),
        {'sqlite_autoincrement': True}
    )
    id = db.Column(db.Integer, primary_key=True, unique=True)
    timestamp = db.Column(db.DateTime, nullable=False)
    sensor_id = db.Column(db.String, db.ForeignKey('sensors.identifier'), nullable=False)
    depth = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f'<{self.timestamp}>'
    
class Temperature(db.Model):
    __tablename__ = "temperature"
    __table_args__ = (
        db.Index('idx_temp_sensor_timestamp', 'sensor_id', 'timestamp'),
        {'sqlite_autoincrement': True}
    )
    id = db.Column(db.Integer, primary_key=True, unique=True)
    timestamp = db.Column(db.DateTime, nullable=False)
    sensor_id = db.Column(db.String, db.ForeignKey('sensors.identifier'), nullable=False)
    temperature = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f'<{self.timestamp}>'