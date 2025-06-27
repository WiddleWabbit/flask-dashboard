from ..models import db
from datetime import datetime, time
import pytz

# Each Weather entry is a forecast of 3 hours

# Temperature values stored in degress c
# Humidity as a percentage (0-100)
# Clouds as a percentage (0-100)
# Rainfall in mm (over the 3h)
# Wind degrees (Meteorological degrees from North)
# Wind Speed (m/sec)
# Human readable summary (normally one word)

class Weather(db.Model):
    __tablename__ = "weather"

    timestamp = db.Column(db.DateTime, primary_key=True, nullable=False)
    temp = db.Column(db.Float, nullable=False)
    temp_min = db.Column(db.Float, nullable=False)
    temp_max = db.Column(db.Float, nullable=False)
    humidity = db.Column(db.Float, nullable=False)
    clouds = db.Column(db.Integer, nullable=False)
    rainfall = db.Column(db.Float, nullable=False)
    wind_deg = db.Column(db.Float, nullable=False)
    wind_speed = db.Column(db.Integer, nullable=False)
    wind_gust = db.Column(db.Float, nullable=False)
    readable = db.Column(db.String(15), nullable=False)

    def __repr__(self):
        return f'<{self.timestamp}>'