from app.models import User


class TestChangePassword(object):
    """A User can change password"""

    def test_change_password_with_correct_credentials(self, client, current_user):
        """Post to /change_password url with correct credentials succeeds"""

        assert current_user.check_password("123123") == True
        res = client.post(
            "/change_password",
            json={"old_password": "123123", "new_password": "abc123"},
        )

        user = User.query.filter_by(email=current_user.email).first()

        assert res.status_code == 200
        assert user.check_password("abc123") == True

    def test_change_password_with_incorrect_password(self, client, current_user):
        """Post to /change_password url with incorrect password fails"""

        res = client.post(
            "/change_password",
            json={"old_password": "definitely-wrong", "new_password": "abc123"},
        )
        user = User.query.filter_by(email=current_user.email).first()
        assert res.status_code == 200
        assert user.check_password("abc123") == False

    def test_change_password_and_login_with_old_password(self, client, current_user):
        """Post to /change_password url and logging in with old password fails"""

        res = client.post(
            "/change_password",
            json={"old_password": "123123", "new_password": "abc123"},
        )

        assert res.status_code == 200

        res = client.post(
            "/login", json={"email": current_user.email, "password": "123123"}
        )

        assert res.status_code == 403
