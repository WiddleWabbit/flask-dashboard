from flask import Blueprint, Flask, request, render_template, url_for, redirect, flash, jsonify
from flask_login import current_user
from app.func import get_setting, sanitise
from app.weather.func import get_weather_data
from app.reports.models import Report
from app.weather.models import Weather
from app.sensors.models import WaterDepth, Temperature, Sensors
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

    # # Build the weather data to pass the report
    # weather_data = Weather.query.filter(Weather.timestamp >= start_date, Weather.timestamp <= end_date).order_by(Weather.timestamp).all()
    # data['weather_data'] = []
    # for record in weather_data:
    #     if local_tz:
    #         local_time = record.timestamp.astimezone(local_tz)
    #         time = local_time.strftime('%a %I:%M %p')
    #     else:
    #         time = record.timestamp.strftime('%a %I:%M %p')
    #     data['weather_data'].append({
    #         'time': time,
    #         'temp': record.temp,
    #         'humidity': record.humidity,
    #         'clouds': record.clouds,
    #         'rainfall': record.rainfall,
    #     })

    data['weather_data'] = []
    data['weather_data'] = get_weather_data(start_date, end_date, local_tz)
    print(data['weather_data'])

    # DATA HERE
    #watertank_data = WaterDepth.query.filter(WaterDepth.timestamp >= start_date, WaterDepth.timestamp <= end_date).order_by(WaterDepth.timestamp).all()

    # import pandas as pd
    
    # def get_tank_depth_data(session: Session, start_date: datetime, end_date: datetime, local_tz=None):
    # # Query only necessary columns for efficiency
    # query = select(
    #     TankDepth.timestamp,
    #     TankDepth.tank_id,
    #     TankDepth.depth
    # ).filter(
    #     TankDepth.timestamp >= start_date,
    #     TankDepth.timestamp <= end_date
    # ).order_by(TankDepth.timestamp)
    
    # # Execute query and load into a DataFrame
    # result = session.execute(query).all()
    # df = pd.DataFrame(result, columns=['timestamp', 'tank_id', 'depth'])
    
    # # Convert timestamps to local timezone if provided
    # if local_tz:
    #     df['timestamp'] = df['timestamp'].dt.tz_convert(local_tz) if df['timestamp'].dt.tz else df['timestamp'].dt.tz_localize('UTC').dt.tz_convert(local_tz)
    
    # # Format timestamps for Chart.js labels
    # df['time'] = df['timestamp'].dt.strftime('%a %I:%M %p')
    
    # # Pivot the DataFrame to create columns for each tank's depth
    # pivot_df = df.pivot(index='time', columns='tank_id', values='depth')
    
    # # Ensure all tank columns (1, 2, 3) exist, filling missing with None
    # for tank_id in [1, 2, 3]:
    #     if tank_id not in pivot_df.columns:
    #         pivot_df[tank_id] = None
    
    # # Prepare Chart.js-compatible data structure
    # data = {
    #     'labels': pivot_df.index.tolist(),
    #     'datasets': [
    #         {'label': 'Tank 1 Depth', 'data': pivot_df[1].tolist(), 'borderColor': 'rgba(75, 192, 192, 1)', 'fill': False},
    #         {'label': 'Tank 2 Depth', 'data': pivot_df[2].tolist(), 'borderColor': 'rgba(255, 99, 132, 1)', 'fill': False},
    #         {'label': 'Tank 3 Depth', 'data': pivot_df[3].tolist(), 'borderColor': 'rgba(54, 162, 235, 1)', 'fill': False}
    #     ]
    # }
    
    # return data

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