from app.models import User


class TestResetPassword(object):
    """A User can reset password"""

    password_reset_salt = "password-reset-salt"

    def test_password_reset(self, client, current_user):
        """Patch to /user/<user_id> url succeeds and password changes"""

        new_password = "123456"
        with client as c:
            reset_url = "/user/" + str(current_user.id)
            res = c.patch(reset_url, json={"new_password": new_password})
            assert res.status_code == 200

        user = User.query.filter_by(id=current_user.id).first()
        assert user.check_password(new_password) == True

    def test_reset_password_with_no_password(self, client, current_user):
        """Patch to /user/<user_id> url with empty password and fails"""

        with client as c:
            reset_url = "/user/" + str(current_user.id)
            res = c.patch(reset_url, json={"new_password": ""})
            assert res.status_code == 400
