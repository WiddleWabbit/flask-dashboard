from app.weather.models import Weather
import pandas as pd

def get_weather_data(timezone, start, end):
    """
    Retrieve weather data from the database for a certain timeframe, ordered by time.

    :param start: Datetime object for the start of period to return.
    :param end: Datetime object for the end of the period to return.
    :param timezone: Pytz object of the local timezome for timestamp conversion.

    :return: The data as a list of tuples.
    """
    try:

        data = Weather.query.with_entities(
            Weather.timestamp, 
            Weather.temp, 
            Weather.humidity, 
            Weather.clouds, 
            Weather.rainfall
        )

        # If only add filters if start and end included
        if start and end:
            data = data.filter(
                Weather.timestamp >= start,
                Weather.timestamp <= end
            )
        
        data = data.order_by(
            Weather.timestamp
        ).all()
        
        # Use Pandas and Dataframe instead

        # Convert to a pandas dataframe so we can perform actions on the entire dataset at once and avoid for loops for large amounts of data
        weather_df = pd.DataFrame(data, columns=['timestamp', 'temp', 'humidity', 'clouds', 'rainfall'])

        # If no data is returned don't try to perform operations on it
        if not weather_df.empty:

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

            # Create response structure
            structured_data = {
                'labels': weather_df['time'].tolist(),
                'datasets': {
                    'temp': weather_df['temp'].tolist(),
                    'humidity': weather_df['humidity'].tolist(),
                    'clouds': weather_df['clouds'].tolist(),
                    'rainfall': weather_df['rainfall'].tolist()
                }
            }

        # If no data was returned
        else:

            structured_data = {
                'labels': [],
                'datasets': {
                    'temp': [],
                    'humidity': [],
                    'clouds': [],
                    'rainfall': []
                }
            }            

        return structured_data

    except Exception as e:
        print(f"Unable to get weather data from database: {e}")
        return None