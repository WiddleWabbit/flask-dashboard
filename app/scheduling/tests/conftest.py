# import pytest
# from app import create_app
# import flask_login
# from flask_login import FlaskLoginClient, login_user, current_user
# from werkzeug.security import generate_password_hash
# from ..models import db, Users, Settings, Zones, Schedules

# def pytest_configure(config):
#     config.addinivalue_line("markers", "reset_db: mark test to reset database before running")

# # Create a new app copy using the test configuration
# # This fixture runs automatically, set to run once per file
# @pytest.fixture(scope="module")
# def app():
    
#     # Create the app
#     app = create_app('app.tests.config.Config')
#     app.test_client_class = FlaskLoginClient

#     with app.app_context():

#         # Do initial setup
#         db.create_all()
#         populate_test_database()

#         # Do the testing here
#         yield app

#         # Cleanup
#         db.session.remove()
#         db.drop_all()

# # Runs when client is called, refreshed for every test
# # Logs out any currently logged in users before running
# @pytest.fixture(scope='function')
# def client(app):
#     if current_user:
#         flask_login.logout_user()
#     return app.test_client()

# # Login a user for this test, log them out afterwards
# @pytest.fixture(scope='function')
# def auth_user(app):
#     with app.test_request_context():
#         yield flask_login.login_user(Users.query.first())
#         flask_login.logout_user()

# # Autouse fixture for tests marked with reset_db
# @pytest.fixture(autouse=True, scope='function')
# def auto_reset_db(request, app):
#     if 'reset_db' in request.node.keywords:
#         with app.app_context():
#             db.drop_all()
#             db.create_all()
#             populate_test_database()
#     yield

# def populate_test_database():
        
#     # Create an admin user
#     password="admin"
#     hashed_password=generate_password_hash(password,method="pbkdf2:sha256")
#     user = Users(username="admin",password=hashed_password,firstname="Firstname",lastname="Lastname",email="test@test.com")
#     db.session.add(user)
#     db.session.commit()

#     # Add a timezone
#     timezone = 'Australia/Perth'
#     db.session.add(Settings(setting="timezone", value=timezone))

#     # Add latitude and longitude
#     long = "115.0"
#     db.session.add(Settings(setting="longitude", value=long))
#     lat = "-30.0"
#     db.session.add(Settings(setting="latitude", value=lat))
#     db.session.commit()