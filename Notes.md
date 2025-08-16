# Notes

## Todo

- Documentation of Modules / Application
- Report for Sensors
- Convert Reports so api page is responsible for loading initial data and call made on page load
- SSL Termination / Setup
- Sunrise Sunset API Integration
  - Integration of this into scheduling
- MQTT Encryption?


## Setup Commands

apt update && apt upgrade -y
apt-get install python3-pip
apt-get install git
apt-get install sqlite3
apt-get install python3-flask
apt-get install python3-flask-sqlalchemy
apt-get install python3-flask-login
apt-get install python3-apscheduler
apt-get install python3-paho-mqtt
apt-get install python3-dotenv
apt-get install gunicorn
apt-get install python3-pandas

## Database

Database is a SQlite database.
- All timestamps are stored in UTC and converted on use.
- None of the database models are timezone aware, so UTC is assumed when pulling them out, and they should always be converted to UTC before going in.

## MQTT

Sensor Data format
```{"time": "2025-07-30 06:22:45", "sensors": { "0": 23.52211, "1": 24.52221 } }```

## Structure

Structure will probably be
- Gunicorn running flask app with a couple of workers, first time run / setup in gunicorn.conf.py file.
- Python running the mqtt file, which runs the mqtt handler and schedules
- Nginx running SSL termination and front end

### Run Commands

gunicorn -c gunicorn.conf.py run:app\
python3 background_tasks.py

## Dev Commands

Various helpful dev commands.

### Run the Shell

flask --app "app:create_app('app.config.Config')" shell

from app.models import db
from app.scheduling.models import Groups, Schedules, Zones, DaysOfWeek, schedule_days, zone_schedules
from app.sensors.models import Sensors, CalibrationModeData, WaterDepth, Temperature

c = CalibrationModeData.query.all()
w = WaterDepth.query.all()
t = Temperature.query.all()

## Includes

Libraries Used:
PYTZ
Pandas
DayJS

Includes Bootstrap Library
Includes Popper Library
https://popper.js.org/docs/v2/
Includes SortableJS Library
https://github.com/SortableJS/Sortable/releases/tag/1.15.6

## Other Notes

https://api.openweathermap.org/data/2.5/forecast?lat=31.88&lon=116.05&units=metric&appid=
https://home.openweathermap.org/api_keys
https://openweathermap.org/forecast5





# Uses the following table arguments:
 1) db.Index so the database keeps a separate ordered index of timestamps.
 This will speed up querying based on timestamp massively when there is a lot of data.
 Will also increase database size, by the size of a extra timestamp and id being stored.
 2) Autoincrement so that indexes are never reused


mqtt.env in app/mqtt
Requires MQTT_USERNAME and MQTT_PASSWORD or attempts unauthed:
MQTT_USERNAME
MQTT_PASSWORD
Default broker_url is localhost
default broker port is 1883
Default client id is flask_mqtt_client
If above three not provided then will either accept at runtime or use default if nothing provided at runtime.

# Flask Manual Data Entry
flask shell
from app import db, Users
from werkzeug.security import generate_password_hash, check_password_hash
password='password'
hashed_password=generate_password_hash(password,method="pbkdf2:sha256")
admin_user = Users(username="admin",password=hashed_password,firstname="Nathan",lastname="Wheat",email="thewheathousehold@gmail.com")
db.session.add(admin_user)
db.session.commit()
quit()
# Check
print(admin_user.id)
# Update 
admin_user.email = 'john_doe@example.com'
db.session.add(admin_user)
db.session.commit()
# Drop all
db.drop_all()
db.create_all()

# Flask Manually Read Database
flask shell
from app import db, Users
user = Users.query.all()
user[0].email
quit()

# Handling Date/Time
from datetime import datetime
import pytz
current_time_utc = datetime.now(pytz.utc)
current_time_utc.isoformat()

# Clear Tables
from app import db, Users, Settings, Groups, Schedules, Zones, DaysOfWeek, schedule_days, zone_schedules
db.drop_all()
db.session.commit()




Settings.__table__.drop(db.engine)


class Parent(db.Model):
    __tablename__= "parents"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    childrens = db.relationship("Child", backref="parents")

    # Use cascade as below to ensure the child is deleted if the parent is deleted
    childrens = db.relationship("Child", backref="parents", cascade="all, delete")

class Child(db.Model):
    __tablename__= "children"    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    parent_id = db.Column(db.Integer, db.ForeignKey("parents.id"), nullable=True)






    sch = Schedules.query.first()
    day = DaysOfWeek.query.all()    
    d = day[2]
    sch.days.append(d)









                // plugins: {
                //     legend: {
                //         display: true,
                //         onClick: (e, legendItem, legend) => {

                //             // Get the default legend click handler
                //             const defaultHandler = Chart.defaults.plugins.legend.onClick;
                //             // Call the default handler to preserve animation
                //             defaultHandler.call(legend, e, legendItem, legend);

                //             // const index = legendItem.datasetIndex;
                //             // const chart = legend.chart;
                //             // const meta = chart.getDatasetMeta(index);

                //             // Custom logic to toggle scale visibility
                //             const chart = legend.chart;
                //             const index = legendItem.datasetIndex;
                //             const meta = chart.getDatasetMeta(index);
                //             const yAxisID = chart.data.datasets[index].yAxisID;

                //             // Update scale display based on dataset visibility
                //             chart.options.scales[yAxisID].display = !meta.hidden;

                //             // Update chart with animation
                //             chart.update({
                //                 duration: 400, // Match default animation duration
                //                 easing: 'easeOutQuart' // Match default easing
                //             });

                //             // // Toggle dataset visibility
                //             // // If meta.hidden is null, use the opposite of current dataset.hidden
                //             // meta.hidden = meta.hidden === null ? !chart.data.datasets[index].hidden : null;
                //             // chart.data.datasets[index].hidden = meta.hidden;

                //             // // Get the yAxisID for this dataset
                //             // const yAxisID = chart.data.datasets[index].yAxisID;

                //             // // For all axes, check if any dataset using this axis is visible
                //             // const anyVisible = chart.data.datasets.some((ds, i) =>
                //             //     ds.yAxisID === yAxisID && !chart.getDatasetMeta(i).hidden
                //             // );
                //             // chart.options.scales[yAxisID].display = anyVisible;

                //             // // Update chart to reflect changes
                //             // //chart.update();
                //             // chart.update({
                //             //     duration: 400, // Match default animation duration
                //             //     easing: 'easeOutQuart' // Match default easing
                //             // });
                //         }
                //     }
                // }




{
    "time": "2025-07-30 06:22:45",
    "sensors": {
        "0": 23.52211,
        "1": 24.52221,
        "2": 44.55323
    }
}