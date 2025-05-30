from flask import Flask
from flask_login import LoginManager

#db = SQLAlchemy()
login_manager = LoginManager()

def create_app(config_file):
    
    app = Flask(__name__, instance_relative_config=True)

    #app.config.from_object('app.config.Config')
    app.config.from_object(config_file)

    #db = SQLAlchemy(app)
    from .models import db
    db.init_app(app)
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "routes.login"
    login_manager.login_message_category = "warning"

    from .models import Users
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(Users, int(user_id))

    from .routes import bp as routes_bp
    app.register_blueprint(routes_bp)

    from .scheduling.routes import bp as scheduling_routes
    app.register_blueprint(scheduling_routes)

  #  from .first_run import firstrun
  #  firstrun(app)

    return app