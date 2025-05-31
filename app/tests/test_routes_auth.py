from unittest.mock import MagicMock, patch
import unittest
from flask_login import logout_user, login_user
from app import login_manager

# Test an actual login
def test_login_success(client):
    resp = client.post("/login", data={"username": "admin", "password": "admin"}, follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/dashboard")

# Test opening the account settings as a logged in user
def test_authed_account_get(client):
    with client.session_transaction() as session:
        # Set a _user_id into the session so we are logged in
        session["_user_id"] = 1
    resp = client.get("/account")
    assert resp.status_code == 200
    assert b"account" in resp.data.lower()
    print("Tested opening account page as a user.")

# Test logging out
@patch('app.routes.logout_user')
def test_logout_success(logout_user, client):
    with client.session_transaction() as session:
        session["_user_id"] = 1
    resp = client.get("/logout", follow_redirects=True)
    assert resp.status_code in (302, 200)
    logout_user.assert_called_once()