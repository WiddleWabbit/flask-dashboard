from flask import Blueprint, Flask, request, render_template, url_for, redirect, flash, current_app
from flask_login import current_user
from app.background_tasks.func import get_forecast

bp = Blueprint('weather_routes', __name__)

# Homepage Test Route
@bp.route("/update_weather")
def update_weather():

    # Check authenticated
    if not current_user.is_authenticated:
        flash('You need to login to manually fetch the weather.', 'danger')
        return redirect(url_for("reports_routes.dashboard"))

    result = get_forecast(current_app)
    if result:
        flash("Weather updated successfully!", "success")
    else:
        flash("Failed to update weather.", "danger")

    return redirect(url_for("reports_routes.dashboard"))