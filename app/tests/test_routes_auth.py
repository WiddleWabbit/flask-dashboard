# Notes

#from flask_login import LoginManager, login_user, logout_user, login_required, current_user
#from unittest.mock import patch, MagicMock
#from ..models import Users, Settings

#@patch("app.routes.get_user")
#@patch("app.routes.check_password_hash")
#@patch("app.routes.login_user")
#mock_login_user, mock_check_password_hash, mock_get_user, 
#mock_user_obj = mock_user()
#mock_get_user.return_value = mock_user_obj
#mock_check_password_hash.return_value = True
#login_user(user)


# Test fetching the login page
def test_login_get(client):
    resp = client.get("/login")
    assert resp.status_code == 200
    assert b"login" in resp.data.lower()
    print("\nTested access to login page.")

# Test an actual login
def test_login_success(client):
    resp = client.post("/login", data={"username": "admin", "password": "admin"}, follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/dashboard")
    #login_user.assert_called_once_with(mock_user_obj)
    print("Tested logging in.")

# Test opening hte account settings as a logged in user
def test_account_authenticated_get(client):
    with client.session_transaction() as session:
        # Set a _user_id into the session so we are logged in
        session["_user_id"] = 1

    resp = client.get("/account")
    assert resp.status_code == 200
    assert b"account" in resp.data.lower()
    print("Tested opening account page as a user.")