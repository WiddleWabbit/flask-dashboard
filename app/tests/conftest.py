import pytest
from app import create_app
from werkzeug.security import generate_password_hash
from ..models import db, Users, Settings

@pytest.fixture(scope="module")
def app():
    # Create a new app copy using the test configuration
    app = create_app('app.tests.config.Config')

    with app.app_context():

        # Do testing
        yield app

@pytest.fixture(scope="function", autouse=True)
def database(app):
     with app.app_context():
        db.create_all()
        populate_test_database()

        yield app
        
        db.session.remove()
        db.drop_all()

@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()

def populate_test_database():
        
        # Create an admin user
        password="admin"
        hashed_password=generate_password_hash(password,method="pbkdf2:sha256")
        user = Users(username="admin",password=hashed_password,firstname="Firstname",lastname="Lastname",email="test@test.com")
        db.session.add(user)
        db.session.commit()

        # Add a timezone
        timezone = 'Australia/Perth'
        db.session.add(Settings(setting="timezone", value=timezone))

        # Add latitude and longitude
        long = "115"
        db.session.add(Settings(setting="longitude", value=long))
        lat = "-30"
        db.session.add(Settings(setting="latitude", value=lat))
        db.session.commit()