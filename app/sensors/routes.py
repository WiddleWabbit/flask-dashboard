from flask import Blueprint, Flask, request, render_template, url_for, redirect, flash
from flask_login import current_user
from app.sensors.models import Sensors, WaterDepth, db
from app.sensors.func import *

bp = Blueprint('sensors_routes', __name__)

# Return the variables to build the configuration page.
def config_sensors():
    data = {}
    data['sensors'] = get_all_sensors()
    if not data['sensors']:
        data['sensors'] = [{"id":1, "name":"", "description":"", "solenoid":""}]
    return data

# Zones Route
@bp.route("/sensors", methods=["GET", "POST"])
def zones():

    if request.method == "GET":
        
        return render_template('sensors.html', data=config_sensors())