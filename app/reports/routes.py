from flask import Blueprint, Flask, request, render_template, url_for, redirect, flash
from app.func import get_setting
from app.reports.models import Report
from app.weather.models import Weather
from datetime import datetime, timedelta
import pytz

bp = Blueprint('reports_routes', __name__)

# Return the variables to build the dashboard page
def config_dashboard():

    # Create dictionary to pass to page rendering
    data = {}
    # Get all the reports
    data['reports'] = Report.query.all()
    # Get the report dates
    start_date = datetime.now(pytz.utc)
    end_date = start_date + timedelta(days=3)
    weather_data = Weather.query.filter(Weather.timestamp >= start_date, Weather.timestamp <= end_date).order_by(Weather.timestamp).all()
    # Get the current timezone
    local_tz = pytz.timezone(get_setting("timezone"))
    if not local_tz:
        flash('No timezone set, using UTC time.', 'warning')
    # Build the weather data to pass the report
    data['weather_data'] = []
    for record in weather_data:

        if local_tz:
            local_time = record.timestamp.astimezone(local_tz)
            time = local_time.strftime('%a %I:%M %p')
        else:
            time = record.timestamp.strftime('%a %I:%M %p')

        data['weather_data'].append({
            'time': time,
            'temp': record.temp,
            'humidity': record.humidity,
            'clouds': record.clouds,
            'rainfall': record.rainfall,
        })

    return data

# Dashboard Route
@bp.route("/dashboard")
def dashboard():

    return render_template('dashboard.html', data=config_dashboard())