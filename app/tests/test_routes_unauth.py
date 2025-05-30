# def mock_user(password_hash="hashed", username="testuser"):
#     user = MagicMock()
#     user.password = password_hash
#     user.username = username
#     user.created_at = "2024-01-01T12:00:00"
#     return user

# def test_login_get(client):
#     resp = client.get("/login")
#     assert resp.status_code == 200
#     assert b"login" in resp.data.lower()

# @patch("app.routes.get_user")
# @patch("app.routes.check_password_hash")
# @patch("app.routes.login_user")
# def test_login_success(mock_login_user, mock_check_password_hash, mock_get_user, client):
#     mock_user_obj = mock_user()
#     mock_get_user.return_value = mock_user_obj
#     mock_check_password_hash.return_value = True

#     resp = client.post("/login", data={"username": "testuser", "password": "pw"}, follow_redirects=False)
#     assert resp.status_code == 302
#     assert resp.headers["Location"].endswith("/dashboard")
#     mock_login_user.assert_called_once_with(mock_user_obj)

# @patch("app.routes.get_user")
# @patch("app.routes.check_password_hash")
# def test_login_failure(mock_check_password_hash, mock_get_user, client):
#     mock_get_user.return_value = None
#     mock_check_password_hash.return_value = False

#     resp = client.post("/login", data={"username": "baduser", "password": "pw"})
#     assert b"Invalid username or password" in resp.data

# def test_account_get(client):
#     resp = client.get("/account")
#     assert resp.status_code == 302
#     assert "/login" in resp.headers["Location"]

# # @patch("app.routes.get_user")
# # @patch("app.routes.update_user")
# # @patch("app.routes.check_password_hash")
# # @patch("app.routes.generate_password_hash")
# # @patch("app.routes.flash")
# # @patch("app.routes.current_user")
# # def test_account_change_password_success(mock_current_user, mock_flash, mock_generate, mock_check, mock_update, mock_get_user, client):
# #     mock_current_user.username = "testuser"
# #     mock_get_user.return_value = mock_user()
# #     mock_check.return_value = True
# #     mock_generate.return_value = "newhash"

# #     resp = client.post("/account?form=change_password", data={
# #         "current_password": "pw",
# #         "new_password": "newpw",
# #         "new_password_conf": "newpw"
# #     }, follow_redirects=False)
# #     mock_update.assert_called_once()
# #     mock_flash.assert_any_call("You've successfully updated your password.", 'success')
# #     assert resp.status_code == 302

# # @patch("app.routes.get_user")
# # @patch("app.routes.flash")
# # @patch("app.routes.current_user")
# # def test_account_change_password_mismatch(mock_current_user, mock_flash, mock_get_user, client):
# #     mock_current_user.username = "testuser"
# #     mock_get_user.return_value = mock_user()

# #     resp = client.post("/account?form=change_password", data={
# #         "current_password": "pw",
# #         "new_password": "a",
# #         "new_password_conf": "b"
# #     }, follow_redirects=False)
# #     mock_flash.assert_any_call('Provided new passwords do not match!', 'danger')
# #     assert resp.status_code == 302

# # @patch("app.routes.get_user")
# # @patch("app.routes.check_password_hash")
# # @patch("app.routes.flash")
# # @patch("app.routes.current_user")
# # def test_account_change_password_wrong_current(mock_current_user, mock_flash, mock_check, mock_get_user, client):
# #     mock_current_user.username = "testuser"
# #     mock_get_user.return_value = mock_user()
# #     mock_check.return_value = False

# #     resp = client.post("/account?form=change_password", data={
# #         "current_password": "wrongpw",
# #         "new_password": "pw",
# #         "new_password_conf": "pw"
# #     }, follow_redirects=False)
# #     mock_flash.assert_any_call('Provided new passwords do not match!', 'danger')
# #     assert resp.status_code == 302

# # @patch("app.routes.get_user")
# # @patch("app.routes.check_password_hash")
# # @patch("app.routes.update_user")
# # @patch("app.routes.flash")
# # @patch("app.routes.current_user")
# # def test_account_update_details_success(mock_current_user, mock_flash, mock_update, mock_check, mock_get_user, client):
# #     mock_current_user.username = "testuser"
# #     mock_get_user.side_effect = [mock_user(), None]  # First for current, second for username check
# #     mock_check.return_value = True

# #     resp = client.post("/account?form=update_details", data={
# #         "current_password_details": "pw",
# #         "username": "newuser",
# #         "firstname": "fn",
# #         "lastname": "ln",
# #         "email": "em"
# #     }, follow_redirects=False)
# #     assert mock_update.call_count == 4
# #     mock_flash.assert_any_call("You've successfully updated your details.", 'success')
# #     assert resp.status_code == 302

# # @patch("app.routes.get_user")
# # @patch("app.routes.check_password_hash")
# # @patch("app.routes.flash")
# # @patch("app.routes.current_user")
# # def test_account_update_details_wrong_password(mock_current_user, mock_flash, mock_check, mock_get_user, client):
# #     mock_current_user.username = "testuser"
# #     mock_get_user.return_value = mock_user()
# #     mock_check.return_value = False

# #     resp = client.post("/account?form=update_details", data={
# #         "current_password_details": "badpw"
# #     }, follow_redirects=False)
# #     mock_flash.assert_any_call('Password entered is incorrect!', 'danger')
# #     assert resp.status_code == 302

# # @patch("app.routes.get_user")
# # @patch("app.routes.check_password_hash")
# # @patch("app.routes.flash")
# # @patch("app.routes.current_user")
# # def test_account_update_details_no_fields(mock_current_user, mock_flash, mock_check, mock_get_user, client):
# #     mock_current_user.username = "testuser"
# #     mock_get_user.return_value = mock_user()
# #     mock_check.return_value = True

# #     resp = client.post("/account?form=update_details", data={
# #         "current_password_details": "pw"
# #     }, follow_redirects=False)
# #     mock_flash.assert_any_call("No fields submitted to change.", 'danger')
# #     assert resp.status_code == 302

# # @patch("app.routes.get_user")
# # @patch("app.routes.check_password_hash")
# # @patch("app.routes.flash")
# # @patch("app.routes.current_user")
# # def test_account_update_details_username_exists(mock_current_user, mock_flash, mock_check, mock_get_user, client):
# #     mock_current_user.username = "testuser"
# #     user1 = mock_user()
# #     user2 = mock_user(username="newuser")
# #     mock_get_user.side_effect = [user1, user2]
# #     mock_check.return_value = True

# #     resp = client.post("/account?form=update_details", data={
# #         "current_password_details": "pw",
# #         "username": "newuser"
# #     }, follow_redirects=False)
# #     mock_flash.assert_any_call('Unable to update. Username already exists.', 'danger')
# #     assert resp.status_code == 302

# # @patch("app.routes.logout_user")
# # def test_logout(mock_logout_user, client):
# #     resp = client.get("/logout", follow_redirects=False)
# #     assert resp.status_code == 302
# #     mock_logout_user.assert_called_once()

# # @patch("app.routes.get_setting")
# # @patch("app.routes.format_isotime")
# # def test_configuration_get(mock_format, mock_get_setting, client):
# #     mock_get_setting.side_effect = ["tz", "lat", "long", "a", "b", "c", "d", "e", "f"]
# #     mock_format.return_value = "time"
# #     resp = client.get("/configuration")
# #     assert resp.status_code == 200
# #     assert b"configuration" in resp.data.lower()

# # @patch("app.routes.current_user")
# # @patch("app.routes.flash")
# # def test_configuration_post_not_authenticated(mock_flash, mock_current_user, client):
# #     mock_current_user.is_authenticated = False
# #     resp = client.post("/configuration", data={})
# #     mock_flash.assert_any_call('You need to login to make modifications.', 'danger')
# #     assert resp.status_code == 302

# # @patch("app.routes.current_user")
# # @patch("app.routes.flash")
# # def test_configuration_post_no_latlong(mock_flash, mock_current_user, client):
# #     mock_current_user.is_authenticated = True
# #     resp = client.post("/configuration", data={})
# #     mock_flash.assert_any_call('Nothing input for latitude or longitude.', 'danger')
# #     assert resp.status_code == 302

# # @patch("app.routes.current_user")
# # @patch("app.routes.set_setting")
# # @patch("app.routes.flash")
# # def test_configuration_post_success(mock_flash, mock_set_setting, mock_current_user, client):
# #     mock_current_user.is_authenticated = True
# #     resp = client.post("/configuration", data={"latitude": "1", "longitude": "2"})
# #     mock_set_setting.assert_any_call("latitude", 1.0)
# #     mock_set_setting.assert_any_call("longitude", 2.0)
# #     mock_flash.assert_any_call("You've successfully updated the coordinates", 'success')
# #     assert resp.status_code == 302