from flask import Blueprint, Flask, request, render_template, url_for, redirect, flash, jsonify
from flask_login import current_user
from app.func import get_setting, sanitise
from app.reports.models import Report
from app.weather.models import Weather
from app.models import db
from datetime import datetime, timedelta
import pytz

bp = Blueprint('reports_routes', __name__)

# Return the variables to build the dashboard page
def config_dashboard():

    # Create dictionary to pass to page rendering
    data = {}
    # Get all the reports
    data['reports'] = Report.query.all()

    # Get the current timezone
    local_tz = pytz.timezone(get_setting("timezone"))
    if not local_tz:
        flash('No timezone set, using UTC time.', 'warning')
        start_date = datetime.now(pytz.utc)
    else:
        start_date = datetime.now(local_tz)
    
    # Get the beginning of the day
    start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = start_date + timedelta(days=3)
    weather_data = Weather.query.filter(Weather.timestamp >= start_date, Weather.timestamp <= end_date).order_by(Weather.timestamp).all()
    
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

# API Route to toggle a report active or inactive
@bp.route("/api/toggle_report")
def api_toggle_report():

    # Check they are logged in
    if not current_user.is_authenticated:
        return jsonify({'error': 'User not authenticated.'}), 400

    report_id = sanitise(request.args.get('report_id'))
    state = sanitise(request.args.get('state'), int)

    # Validate the fields
    if not report_id:
        return jsonify({'error': 'Invalid report ID.'}), 400
    if not isinstance(state, int):
        return jsonify({'error': 'State not Int'}), 400
    if state not in [0, 1]:
        return jsonify({'error': 'Not Boolean'}), 400
    
    # Find the report and update it's active state
    report = Report.query.filter_by(id=report_id).first()
    if report:
        report.active = state
        db.session.commit()
        return jsonify({'success': f'Updated report {report_id} active to {state}'}), 200
    else:
        return jsonify({'error': 'Unable to find report ID.'}), 400


# Weather API Update Route
@bp.route("/api/weather_report")
def api_weather_report():

    start_date = sanitise(request.args.get('start'))
    end_date = sanitise(request.args.get('end'))
    
    # Convert string dates to datetime objects
    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d') if start_date else None
        end_date = datetime.strptime(end_date, '%Y-%m-%d') if end_date else None
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

    # Query the database
    query = Weather.query
    if start_date:
        query = query.filter(Weather.timestamp >= start_date)
    if end_date:
        query = query.filter(Weather.timestamp <= end_date)
    data = query.all()

    local_tz = pytz.timezone(get_setting("timezone"))
    if not local_tz:
        flash('No timezone set, using UTC time.', 'warning')

    weather_data = []
    for record in data:
        
        if local_tz:
            local_time = record.timestamp.astimezone(local_tz)
            time = local_time.strftime('%a %I:%M %p')
        else:
            time = record.timestamp.strftime('%a %I:%M %p')

        weather_data.append({
            'time': time,
            'temp': record.temp,
            'humidity': record.humidity,
            'clouds': record.clouds,
            'rainfall': record.rainfall,
        })
    
    # Format data for Chart.js
    return jsonify(weather_data)