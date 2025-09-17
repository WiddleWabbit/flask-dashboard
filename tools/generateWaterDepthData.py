from datetime import datetime, timedelta
from random import choice
from app.models import db  # Replace 'app' with your Flask app's module name
from app.sensors.models import WaterDepth, Sensors  # Replace 'models' with your models' module name

# Configuration
num_entries = 300  # Number of entries to generate
start_depth = 100.0  # Starting water depth
start_time = datetime(2025, 9, 17, 0, 0)  # Starting timestamp (adjust as needed)
sensor_id = Sensors.query.first().identifier  # Get the first sensor's identifier

# Ensure a sensor exists
if not sensor_id:
    print("No sensors found. Please create a sensor in the Sensors table first.")
    exit()

# Generate water depth entries
current_depth = start_depth
current_time = start_time
depth_changes = [-1, 0, 1]  # Possible changes: decrease, stay, increase

for i in range(num_entries):
    # Create a new WaterDepth entry
    entry = WaterDepth(
        timestamp=current_time,
        sensor_id=sensor_id,
        value=current_depth
    )
    db.session.add(entry)
    # Update values for the next entry
    change = choice(depth_changes)  # Randomly choose -1, 0, or 1
    current_depth = max(0, current_depth + change)  # Ensure depth doesn't go negative
    current_time += timedelta(minutes=1)  # Increment timestamp by 1 minute

# Commit all entries to the database
try:
    db.session.commit()
    print(f"Successfully added {num_entries} WaterDepth entries.")
except Exception as e:
    db.session.rollback()
    print(f"Error committing to database: {e}")