from flask import Blueprint, Flask, request, render_template, url_for, redirect, flash, jsonify
from flask_login import current_user
from app.func import get_setting, sanitise
from app.weather.func import get_weather_data
from app.sensors.func import get_watertank_data
from app.reports.models import Report
from app.weather.models import Weather
from app.sensors.models import WaterDepth, Temperature, Sensors
from app.models import db
from datetime import datetime, timedelta
import pytz
import time

bp = Blueprint('reports_routes', __name__)

# Return the variables to build the dashboard page
def config_dashboard():

    # Create dictionary to pass to page rendering
    data = {}
    # Get all the reports
    data['reports'] = Report.query.all()

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

    start_timer = time.perf_counter()

    start_date = sanitise(request.args.get('start'))
    end_date = sanitise(request.args.get('end'))
    
    # Convert string dates to datetime objects
    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d') if start_date else None
        end_date = datetime.strptime(end_date, '%Y-%m-%d') if end_date else None
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

    local_tz = pytz.timezone(get_setting("timezone"))
    if not local_tz:
        flash('No timezone set, using UTC time.', 'warning')
        local_tz = pytz.UTC
    
    weather_data = get_weather_data(local_tz, start_date, end_date)
    
    end_timer = time.perf_counter()
    execution_time = end_timer - start_timer
    
    print(f"Function took {execution_time:.4f} seconds to run")
    
    # Format data for Chart.js
    return jsonify(weather_data)

# Weather API Update Route
@bp.route("/api/watertank_report")
def api_watertank_report():

    start_timer = time.perf_counter()

    start_date = sanitise(request.args.get('start'))
    end_date = sanitise(request.args.get('end'))
    
    # Convert string dates to datetime objects
    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d') if start_date else None
        end_date = datetime.strptime(end_date, '%Y-%m-%d') if end_date else None
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

    local_tz = pytz.timezone(get_setting("timezone"))
    if not local_tz:
        flash('No timezone set, using UTC time.', 'warning')
        local_tz = pytz.UTC

    watertank_data = get_watertank_data(local_tz, start_date, end_date)
    
    end_timer = time.perf_counter()
    execution_time = end_timer - start_timer
    
    print(f"Function took {execution_time:.4f} seconds to run")
    
    # Format data for Chart.js
    return jsonify(watertank_data)