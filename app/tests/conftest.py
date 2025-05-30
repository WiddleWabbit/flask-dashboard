import pytest
from app import create_app
from werkzeug.security import generate_password_hash
from ..models import db, Users, Settings

@pytest.fixture(scope="function")
def app():
    app = create_app('app.tests.config.Config')

    with app.app_context():
        db.create_all()

        password="admin"
        hashed_password=generate_password_hash(password,method="pbkdf2:sha256")
        user = Users(username="admin",password=hashed_password,firstname="Firstname",lastname="Lastname",email="test@test.com")
        db.session.add(user)
        db.session.commit()

        timezone = 'Australia/Perth'
        db.session.add(Settings(setting="timezone", value=timezone))

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()