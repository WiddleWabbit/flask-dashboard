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

# Test fetching the configuration page
def test_configuration_get(client):
    resp = client.get("/configuration")
    assert resp.status_code == 200
    assert b"configuration" in resp.data.lower()

# Test fetching the account page
def test_account_get(client):
    resp = client.get("/account")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]

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