from flask_sqlalchemy import SQLAlchemy
from app.models import db

class Sensors(db.Model):
    __tablename__ = "sensors"
    __table_args__ = {'sqlite_autoincrement': True}
    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String, nullable=False)
    topic = db.Column(db.String, nullable=False)
    calibration_factor = db.Column(db.Float, nullable=False)
    type = db.Column(db.String, nullable=False)

    def __repr__(self):
        return f'<{self.name}>'

class WaterDepth(db.Model):
    __tablename__ = "waterdepth"
    __table_args__ = (
        db.Index('idx_depth_sensor_timestamp', 'sensor_id', 'timestamp'),
        {'sqlite_autoincrement': True}
    )
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False)
    sensor_id = db.Column(db.String, db.ForeignKey('sensors.id'), nullable=False)
    depth = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f'<{self.timestamp}>'
    
class Temperature(db.Model):
    __tablename__ = "temperature"
    __table_args__ = (
        db.Index('idx_temp_sensor_timestamp', 'sensor_id', 'timestamp'),
        {'sqlite_autoincrement': True}
    )
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False)
    sensor_id = db.Column(db.String, db.ForeignKey('sensors.id'), nullable=False)
    temperature = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f'<{self.timestamp}>'