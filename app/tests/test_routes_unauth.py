# Test fetching the homepage
def test_home_get(client):
    resp = client.get("/")
    assert resp.status_code == 200

# Test fetching the dashboard page
def test_dashboard_get(client):
    resp = client.get("/dashboard")
    assert resp.status_code == 200

# Test fetching the login page
def test_login_get(client):
    resp = client.get("/login")
    assert resp.status_code == 200
    assert b"login" in resp.data.lower()

# Test going to the logout page while not logged in.
def test_logout_get(client):
    resp = client.get("/logout")
    assert resp.status_code == 302
    assert "/login" in resp.headers["location"]

# Test fetching the configuration page
def test_configuration_get(client):
    resp = client.get("/configuration")
    assert resp.status_code == 200
    assert b"configuration" in resp.data.lower()

# Test form time settings submission on configuration page
def test_unauth_config_time_post(client):
    resp = client.post("/configuration?form=time_settings", data={"latitude": -30})
    assert resp.status_code == 403
    assert b"alert" in resp.data.lower()

# Test fetching the account page
def test_account_get(client):
    resp = client.get("/account")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]

# Test form update details submission on account page
def test_unauth_account_update_post(client):
    resp = client.post("/account?form=update_details", data={"username": "test", "current_password_details": "admin"})
    assert resp.status_code == 302
    assert "/login" in resp.headers["location"]

# Test form change password submission on account page
def test_unauth_account_changepass_post(client):
    resp = client.post("/account?form=change_password", data={"current_password": "admin", "new_password": "admin1", "new_password_conf": "admin1"})
    assert resp.status_code == 302
    assert "/login" in resp.headers["location"]

# Test fetching main css file
def test_appcss_get(client):
    resp = client.get('/static/css/app.css')
    assert resp.status_code == 200
    assert b"main css" in resp.data.lower()

# Test fetching bootstrap css file
def test_bootstrapcss_get(client):
    resp = client.get('/static/css/bootstrap.min.css')
    assert resp.status_code == 200
    assert b"bootstrap" in resp.data.lower()

# Test fetching bootstrap js file
def test_bootstrapjs_get(client):
    resp = client.get('/static/js/bootstrap.bundle.min.js')
    assert resp.status_code == 200
    assert b"bootstrap" in resp.data.lower()