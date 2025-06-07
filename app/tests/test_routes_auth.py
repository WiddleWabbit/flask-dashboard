from unittest.mock import MagicMock, patch
import unittest
from flask_login import logout_user, login_user, current_user
from app import login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from ..models import db, Users, Settings
import pytest

# Test an actual login
@patch('app.routes.login_user')
def test_login_success(login_user, client):
    resp = client.post("/login?form=login", data={"username": "admin", "password": "admin"}, follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/dashboard")
    login_user.assert_called_once()

# Test login with incorrect details
@pytest.mark.reset_db
def test_login_incorrect_details(client):
    resp = client.post("/login?form=login", data={"username": "admin", "password": "wrongpassword"}, follow_redirects=False)
    assert resp.status_code == 403
    assert b"alert" in resp.data.lower()

# Test the login with user already logged in
@pytest.mark.reset_db
def test_login_alreadyloggedin(client, auth_user):
    resp = client.post("/login?form=login", data={"username": "admin", "password": "admin2"}, follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/dashboard")

# Test login with non-existent user
@pytest.mark.reset_db
def test_login_nonexistent_user(client):
    resp = client.post("/login?form=login", data={"username": "nonexistent", "password": "irrelevant"}, follow_redirects=False)
    assert resp.status_code == 403
    assert b"alert" in resp.data.lower()

# Test logging out
@pytest.mark.reset_db
@patch('app.routes.logout_user')
def test_logout_success(logout_user, client, auth_user):
    resp = client.get("/logout", follow_redirects=True)
    assert resp.status_code in (302, 200)
    logout_user.assert_called_once()

# Test opening the account settings as a logged in user
@pytest.mark.reset_db
def test_account_get(client, auth_user):
    resp = client.get("/account")
    assert resp.status_code == 200
    assert b"account" in resp.data.lower()

# Test form update details submission on account page
@pytest.mark.reset_db
def test_account_update(client, auth_user):
    resp = client.post("/account?form=update_details", data={
        "username": "new_username", 
        "current_password_details": "admin", 
        "firstname": "new_firstname",
        "lastname" : "new_lastname",
        "email" : "new_test@test.com"
        })
    # Confirm the response
    assert resp.status_code == 302
    updated_user = Users.query.filter_by(username="new_username").all()
    assert len(updated_user) == 1
    # Confirm the user's details were updated
    updated_user = updated_user[0]
    assert updated_user.firstname == "new_firstname"
    assert updated_user.lastname == "new_lastname"
    assert updated_user.email == "new_test@test.com"

# Test form update details submission on account page with duplicate username
@pytest.mark.reset_db
def test_account_dup_user_update(client, auth_user):

    hashed_password=generate_password_hash("dup_admin",method="pbkdf2:sha256")
    user = Users(username="admin1",password=hashed_password,firstname="Firstname1",lastname="Lastname1",email="dup_test@test.com")
    db.session.add(user)
    db.session.commit()

    with client.session_transaction() as session:
        session["_user_id"] = 1

    resp = client.post("/account?form=update_details", data={
        "username": "admin1", 
        "current_password_details": "admin", 
        }, follow_redirects=False)
    # Confirm the response
    assert resp.status_code == 422
    failed_update_user = Users.query.filter_by(username="admin").all()
    assert len(failed_update_user) == 1

# Test form update details submission on account page with duplicate email
@pytest.mark.reset_db
def test_account_dup_email_update(client, auth_user):

    hashed_password=generate_password_hash("dup_admin",method="pbkdf2:sha256")
    user = Users(username="admin1",password=hashed_password,firstname="Firstname1",lastname="Lastname1",email="dup_test@test.com")
    db.session.add(user)
    db.session.commit()

    with client.session_transaction() as session:
        session["_user_id"] = 1

    resp = client.post("/account?form=update_details", data={
        "email": "dup_test@test.com", 
        "current_password_details": "admin", 
        }, follow_redirects=True)
    # Confirm the response
    assert resp.status_code == 422
    failed_update_user = Users.query.filter_by(email="dup_test@test.com").all()
    assert len(failed_update_user) == 1

# Test form update details submission on account page with wrong password
@pytest.mark.reset_db
def test_account_wrongpass_update(client, auth_user):
    resp = client.post("/account?form=update_details", data={
        "email": "new_email@test.com", 
        "current_password_details": "wrongpassword", 
        }, follow_redirects=False)
    # Confirm the response
    assert resp.status_code == 403
    failed_update_user = Users.query.filter_by(email="new_email@test.com").all()
    assert len(failed_update_user) == 0

# Test form change password submission on account page
@pytest.mark.reset_db
def test_account_changepass_success(client, auth_user):
    resp = client.post("/account?form=change_password", data={"current_password": "admin", "new_password": "admin1", "new_password_conf": "admin1"})
    assert resp.status_code == 302
    assert "/account" in resp.headers["location"]

    updated_user = Users.query.filter_by(username="admin").first()
    updated_password = updated_user.password
    assert check_password_hash(updated_password, "admin1") == True

# Test form change password submission on account page
@pytest.mark.reset_db
def test_account_changepass_failed_confirmation(client, auth_user):
    resp = client.post("/account?form=change_password", data={"current_password": "admin", "new_password": "admin1", "new_password_conf": "different"})
    assert resp.status_code == 403

    updated_user = Users.query.filter_by(username="admin").first()
    updated_password = updated_user.password
    assert check_password_hash(updated_password, "admin1") == False

# Test form change password submission on account page
@pytest.mark.reset_db
def test_account_changepass_wrong_password(client, auth_user):
    resp = client.post("/account?form=change_password", data={"current_password": "incorrectpassword", "new_password": "admin1", "new_password_conf": "admin1"})
    assert resp.status_code == 302
    assert "/account" in resp.headers["location"]

    updated_user = Users.query.filter_by(username="admin").first()
    updated_password = updated_user.password
    assert check_password_hash(updated_password, "incorrectpassword") == False

# Test opening the account settings as a logged in user
def test_configuration_get(client, auth_user):
    resp = client.get("/configuration")
    assert resp.status_code == 200
    assert b"configuration" in resp.data.lower()

# Test form submission on configuration page
@pytest.mark.reset_db
def test_configuration_latitude_success_both(client, auth_user):
    resp = client.post("/configuration?form=time_settings", data={"latitude": -50.0, "longitude": 125})
    assert resp.status_code == 302
    assert "/configuration" in resp.headers["location"]
    assert Settings.query.filter_by(setting="latitude").first().value == "-50.0"
    assert Settings.query.filter_by(setting="longitude").first().value == "125.0"

# Test form submission on configuration page
@pytest.mark.reset_db
def test_configuration_latitude_success_single(client, auth_user):
    resp = client.post("/configuration?form=time_settings", data={"latitude": -50.0})
    assert resp.status_code == 302
    assert "/configuration" in resp.headers["location"]
    assert Settings.query.filter_by(setting="latitude").first().value == "-50.0"
    assert Settings.query.filter_by(setting="longitude").first().value == "115.0"

# Test form submission on configuration page
@pytest.mark.reset_db
def test_configuration_latitude_invalid(client, auth_user):
    resp = client.post("/configuration?form=time_settings", data={"latitude": "invalid", "longitude": "invalid"})
    assert resp.status_code == 302
    assert "/configuration" in resp.headers["location"]
    assert Settings.query.filter_by(setting="latitude").first().value == "-30.0"