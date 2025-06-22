from flask import Flask
from flask_login import LoginManager
from app.mqtt.mqtt_handler import MQTTHandler

login_manager = LoginManager()

def create_app(config_file):
    """
    App factory function to create the application.
    Utilises a configuration parameter with a absolute reference to the configuration of the app
    so that we can also use it for testing with another configuration/test database.

    :param config_file: The config file import as a string. I.e. app.config.Config
    :return: The app object.
    """

    app = Flask(__name__, instance_relative_config=True)

    app.config.from_object(config_file)

    from .models import db
    db.init_app(app)
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "routes.login"
    login_manager.login_message_category = "warning"
    login_manager.session_protection = "strong"

    from .models import Users
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(Users, int(user_id))

    from .routes import bp as routes_bp
    app.register_blueprint(routes_bp)

    from .scheduling.routes import bp as scheduling_routes
    app.register_blueprint(scheduling_routes)    

    # Initialise the MQTT Handler
    app.mqtt_handler = MQTTHandler()

    return app