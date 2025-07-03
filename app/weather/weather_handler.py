import requests
from datetime import datetime
from app.func import get_setting, timestamp_to_db
from .models import Weather
from dotenv import load_dotenv
from pathlib import Path
import logging
import os

class WeatherService:
    def __init__(self):
        # Get the logger
        self.logger = logging.getLogger(__name__)
        # Load environment variables
        env_path = Path(__file__).parent / "weather.env"
        load_dotenv(dotenv_path=env_path)
        self.apikey = os.getenv("OPEN_WEATHER_MAP_APIKEY")
        # Prepare static variables
        self.base_url = "https://api.openweathermap.org/data/2.5/forecast"
        self.units = "metric"
        self.cnt = 40
        # Fetch dynamic variables from db
        self.lat = get_setting("latitude")
        self.long = get_setting("longitude")

        # Validate Data
        if not self.apikey:
            raise ValueError("API key is required and cannot be empty")
        if not self.lat:
            raise ValueError("Latitude is required and cannot be empty")
        if not self.long:
            raise ValueError("Longitude is required and cannot be empty")
        
        self.session = requests.Session()
        
    def fetch_weather(self):
        """Fetch weather data"""
        try:
            params = {"lat": self.lat, "lon": self.long, "cnt": self.cnt, "appid": self.apikey, "units": self.units}
            response = self.session.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            return data
        except requests.exceptions.RequestException as e:
            print(f"Error fetching weather: {e}")
            return False
        
    def save_to_db(self, weather_data, db_session):
        """Save weather data to the database."""
        if weather_data:
            try:
                for forecast in weather_data['list']:

                    # Convert unix timestamp (utc) to datetime object (utc)
                    timestamp = timestamp_to_db(forecast["dt"])
                    if not timestamp:
                        self.logger.error(f"Error processing timestamp of {forecast['dt']}")
                    # Find existing weather data
                    existing = db_session.get(Weather, timestamp)

                    if existing:
                        # Update existing weather data with more recent forecast
                        existing.temp = forecast.get("main", {}).get("temp", 0)
                        existing.temp_min = forecast.get("main", {}).get("temp_min", 0)
                        existing.temp_max = forecast.get("main", {}).get("temp_max", 0)
                        existing.humidity = forecast.get("main", {}).get("humidity", 0)
                        existing.clouds = forecast.get("clouds", {}).get("all", 0)
                        existing.wind_deg = forecast.get("wind", {}).get("deg", 0)
                        existing.wind_speed = forecast.get("wind", {}).get("speed", 0)
                        existing.wind_gust = forecast.get("wind", {}).get("gust", 0)
                        existing.rainfall = forecast.get("rain", {}).get("3h", 0)
                        existing.readable = forecast.get("weather", [{}])[0].get("main", "Blank")
                        self.logger.info(f"Updating existing weather data for {forecast['dt']}")
                    else:
                        # Add new weather data
                        weather_entry = Weather(
                            timestamp = timestamp,
                            temp = forecast.get("main", {}).get("temp", 0),
                            temp_min = forecast.get("main", {}).get("temp_min", 0),
                            temp_max = forecast.get("main", {}).get("temp_max", 0),
                            humidity = forecast.get("main", {}).get("humidity", 0),
                            clouds = forecast.get("clouds", {}).get("all", 0),
                            wind_deg = forecast.get("wind", {}).get("deg", 0),
                            wind_speed = forecast.get("wind", {}).get("speed", 0),
                            wind_gust = forecast.get("wind", {}).get("gust", 0),
                            rainfall = forecast.get("rain", {}).get("3h", 0),
                            readable = forecast.get("weather", [{}])[0].get("main", "Blank")
                        )
                        db_session.add(weather_entry)
                        self.logger.info(f"Added weather data for {timestamp}")

                # Save the database changes
                db_session.commit()
                self.logger.info(f"Saved weather data")
                return True

            except Exception as e:
                db_session.rollback()
                print(f"Error saving to database: {e}")
                return False
            finally:
                # Ensure session is closed
                db_session.close()

    def close(self):
        """Close the HTTP session."""
        self.session.close()

    def __enter__(self):
        """Support for context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ensure resources are cleaned up."""
        self.close()