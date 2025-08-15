from flask import Blueprint, Flask, request, render_template, url_for, redirect, flash, jsonify
from app.func import get_setting
from app.weather.models import Weather
from datetime import datetime, timedelta
import pytz
import pandas as pd

#####################################################################################################################
# Convert to using Pandas for transformation
# Have this function called instead of locally in reports routes
# Have data loaded on page load, rather than sent initially

def get_weather_data(start, end, timezone):
    """
    Retrieve weather data from the database for a certain timeframe, ordered by time.

    :param start: Datetime object for the start of period to return.
    :param end: Datetime object for the end of the period to return.
    :param timezone: Pytz object of the local timezome for timestamp conversion.

    :return: The data as a list of tuples.
    """
    try:

        # Fetch the weather data
        # Query only what we want to return
        data = Weather.query.with_entities(
            Weather.timestamp, 
            Weather.temp, 
            Weather.humidity, 
            Weather.clouds, 
            Weather.rainfall
        ).filter(
            Weather.timestamp >= start,
            Weather.timestamp <= end
        ).order_by(
            Weather.timestamp
        ).all()
        
        # Use Pandas and Dataframe instead

        # Convert to a pandas dataframe so we can perform actions on the entire dataset at once and avoid for loops for large amounts of data
        weather_df = pd.DataFrame(data, columns=['timestamp', 'temp', 'humidity', 'clouds', 'rainfall'])

        if timezone:
            # Database models are not saved timezone aware, all database models save in UTC time. Per this we assume it's in UTC.
            # We are using Pandas Datetime methods here as these are vectorized and process all the data at the same time rather than iterating through it.
            # If we used something like .apply() it would perform per row instead, just like a for loop.
            # Functions in use are:
            # .dt() Access the vectorized timezone functions of Pandas library
            # .tz_localize('UTC') assigns a timezone to a timezone naive timestamp making them aware.
            # .tz_convert() converts an timezone aware timestamp to another timezone
            weather_df['timestamp'] = weather_df['timestamp'].dt.tz_localize('UTC').dt.tz_convert(timezone)
        
        # Create a new column in the Dataframe called time. 
        # Same as above modify the entire lot at the same time rather than iterating through them by using vectorized functions from pandas
        # Pandas functions in use here:
        # .dt() Access the vectorized timezone functions of the Pandas library.
        # strftime() Convert 
        weather_df['time'] = weather_df['timestamp'].dt.strftime('%a %I:%M %p')

        # ADDITIONAL CONSIDERATIONS
        # Aggregate data? Reduce the data down to lower resolution
        # df['time'] = df['timestamp'].dt.floor('5min').dt.strftime('%a %I:%M %p')
        # Aggregate data in the SQL query

        # Use Pandas Pivots and builtin timezone conversions for optimisation

        # weather_data = []
        # for timestamp, temp, humidity, clouds, rainfall in data:
        #     if timezone:
        #         local_time = timestamp.astimezone(timezone)
        #         time = local_time.strftime('%a %I:%M %p')
        #     else:
        #         time = timestamp.strftime('%a %I:%M %p')
        #     weather_data.append({
        #         'time': time,
        #         'temp': temp,
        #         'humidity': humidity,
        #         'clouds': clouds,
        #         'rainfall': rainfall,
        #     })

        structured_data = weather_df.to_dict('records')

        return structured_data

    except Exception as e:
        print(f"Unable to get weather data from database: {e}")
        return None