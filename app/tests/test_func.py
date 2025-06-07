import pytest
from unittest.mock import patch, MagicMock
from app import func
from ..models import db, Settings

@pytest.fixture
def mock_user():
    user = MagicMock()
    user.username = "testuser"
    user.email = "test@example.com"
    user.some_setting = "old_value"
    return user

@pytest.fixture
def mock_setting():
    setting = MagicMock()
    setting.setting = "timezone"
    setting.value = "UTC"
    return setting

def test_get_user_found(monkeypatch, mock_user):
    query = MagicMock()
    query.filter_by.return_value.first.return_value = mock_user
    monkeypatch.setattr(func.Users, "query", query)
    user = func.get_user("testuser")
    assert user.username == "testuser"

def test_get_user_not_found(monkeypatch):
    query = MagicMock()
    query.filter_by.return_value.first.return_value = None
    monkeypatch.setattr(func.Users, "query", query)
    user = func.get_user("nouser")
    assert user is None

def test_update_user_success(monkeypatch, mock_user):
    monkeypatch.setattr(func, "get_user", lambda username: mock_user)
    db_mock = MagicMock()
    monkeypatch.setattr(func, "db", db_mock)
    result = func.update_user("testuser", "some_setting", "new_value")
    assert result is True
    assert mock_user.some_setting == "new_value"
    db_mock.session.commit.assert_called_once()

def test_update_user_fail(monkeypatch):
    monkeypatch.setattr(func, "get_user", lambda username: None)
    db_mock = MagicMock()
    monkeypatch.setattr(func, "db", db_mock)
    result = func.update_user("nouser", "some_setting", "new_value")
    assert result is False

def test_get_setting_found(monkeypatch, mock_setting):
    query = MagicMock()
    query.filter_by.return_value.first.return_value = mock_setting
    monkeypatch.setattr(func.Settings, "query", query)
    value = func.get_setting("timezone")
    assert value == "UTC"

def test_get_setting_not_found(monkeypatch):
    query = MagicMock()
    query.filter_by.return_value.first.return_value = None
    monkeypatch.setattr(func.Settings, "query", query)
    value = func.get_setting("notfound")
    assert value is None

def test_set_setting_update(monkeypatch, mock_setting):
    query = MagicMock()
    query.filter_by.return_value.first.return_value = mock_setting
    monkeypatch.setattr(func.Settings, "query", query)
    db_mock = MagicMock()
    monkeypatch.setattr(func, "db", db_mock)
    result = func.set_setting("timezone", "Europe/London")
    assert result is True
    assert mock_setting.value == "Europe/London"
    db_mock.session.commit.assert_called_once()

@pytest.mark.parametrize("setting,value,result", [
    ("test_setting", "test_val", True),
    ("ran_setting", 44, False),
    ("test", "", False),
    ("3.14", 22.1, False),
    ("", "test_value", False),
    (123, 123, False),
])
def test_set_setting_create(setting, value, result):
    function_result = func.set_setting(setting, value)
    if result == True:
        assert function_result is True
        assert type(Settings.query.filter_by(setting=setting).first().value) == str
        assert Settings.query.filter_by(setting=setting).first().value == value
    else:
        assert function_result is False
        assert len(Settings.query.filter_by(setting=setting).all()) == 0    

def test_format_isotime(monkeypatch):
    monkeypatch.setattr(func, "get_setting", lambda name: "UTC")
    iso_time = "2024-01-01T12:34:56+00:00"
    result = func.format_isotime(iso_time, "%H:%M")
    assert result == "12:34"

def test_to_isotime(monkeypatch):
    monkeypatch.setattr(func, "get_setting", lambda name: "UTC")
    local_time = "2024-01-01 12:00:00"
    result = func.to_isotime(local_time)
    assert result.startswith("2024-01-01T12:00:00+00:00")

@pytest.mark.parametrize("value,expected_type,expected", [
    ("  hello <b>world</b>  ", str, "hello &lt;b&gt;world&lt;/b&gt;"),
    ("42", int, 42),
    (22.5, float, 22.5),
    ("", str, False),
    ("   ", str, False),
    ("&nbsp;", str, "&amp;nbsp;"),
    ("   ", int, False),
    ("notanint", int, False),
    ("3.14", float, 3.14),
    ("notafloat", float, False),
    (123, str, False),
])
def test_sanitise(value, expected_type, expected):
    assert func.sanitise(value, expected_type) == expected

def test_update_status_messages_all_success():
    results = {"username": True, "email": True}
    messages = func.update_status_messages(results)
    assert "success" in messages
    assert messages["success"] == "Successfully updated: username, email."
    assert "danger" not in messages

def test_update_status_messages_all_fail():
    results = {"username": False, "email": False}
    messages = func.update_status_messages(results)
    assert "danger" in messages
    assert messages["danger"] == "Failed to update: username, email."
    assert "success" not in messages

def test_update_status_messages_mixed():
    results = {"username": True, "email": False, "firstname": True, "lastname": False}
    messages = func.update_status_messages(results)
    assert "success" in messages
    assert "danger" in messages
    assert messages["success"] == "Successfully updated: username, firstname."
    assert messages["danger"] == "Failed to update: email, lastname."

def test_update_status_messages_empty():
    results = {}
    messages = func.update_status_messages(results)
    assert messages == {}

def test_update_status_messages_string():
    results = "Test"
    messages = func.update_status_messages(results)
    assert messages == False

def test_update_status_messages_list():
    results = ["Test", 24]
    messages = func.update_status_messages(results)
    assert messages == False

def test_update_status_messages_single_success():
    results = {"username": True}
    messages = func.update_status_messages(results)
    assert messages == {"success": "Successfully updated: username."}

def test_update_status_messages_single_fail():
    results = {"username": False}
    messages = func.update_status_messages(results)
    assert messages == {"danger": "Failed to update: username."}

@pytest.mark.parametrize("results, expected", [
    ({"Zone 1":True, "Zone 2": True}, {"warning": 'Successfully deleted: Zone 1, Zone 2.'}),
    ({"Zone 3":True}, {"warning": 'Successfully deleted: Zone 3.'}),
    ({"Zone 1": False}, {"danger": 'Failed to delete: Zone 1.'}),
    ({"Empty":""}, False),
    ("", False),
    ({"":"", "Fail":False}, False),
    (24, False),
    ({24: 12}, False),
    ([24, 18], False),
])
def test_delete_status_messages(results, expected):
    messages = func.delete_status_messages(results)
    print(messages)
    assert messages == expected
    

@pytest.mark.parametrize("messages, expected", [
    ({"success":"Test Success Message", "failure":"Test Failure Message"}, True),
    ({"danger":"Test Danger Message"}, True),
    ({"info":"Test Info Message"}, True),
    ({"success":""}, False),
    ("", False),
    ({"":"", "Fail":"Failure"}, False),
    (24, False),
    ({24: 14}, False),
    ({24, 14, 25}, False),
])
def test_flash_status_messages(app, messages, expected):
    with patch("app.func.flash") as mock_flash:
        #with app.app_context():
        result = func.flash_status_messages(messages)
        assert result == expected
        if result is True and isinstance(messages, dict):
            for key, val in messages.items():
                mock_flash.assert_any_call(val, key)

def test_update_sun_times_success(monkeypatch):
    monkeypatch.setattr(func, "get_setting", lambda name: "1" if name in ("latitude", "longitude") else "UTC")
    monkeypatch.setattr(func, "set_setting", lambda name, value: True)
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "results": {
            "sunrise": "1700000000",
            "sunset": "1700003600",
            "dawn": "1700000100",
            "dusk": "1700003700",
            "first_light": "1700000050",
            "last_light": "1700003750"
        }
    }
    monkeypatch.setattr(func.requests, "get", lambda url: mock_response)
    assert func.update_sun_times() is True

def test_update_sun_times_fail(monkeypatch):
    monkeypatch.setattr(func, "get_setting", lambda name: None)
    monkeypatch.setattr(func.requests, "get", lambda url: (_ for _ in ()).throw(Exception("fail")))
    assert func.update_sun_times() is False
