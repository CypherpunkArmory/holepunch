from app.models import User


class TestChangePassword(object):
    """A User can change password"""

    new_password = "abcdef"

    def test_change_password_with_correct_credentials(self, client, current_user):
        """Patch to /user/<user_id> url succeeds and password changes successfully"""

        update_user_url = "/user/" + str(current_user.id)
        res = client.patch(
            update_user_url,
            json={
                "data": {"type": "user", "attributes": {"password": self.new_password}}
            },
        )

        user = User.query.filter_by(email=current_user.email).first()
        assert res.status_code == 200
        assert user.check_password(self.new_password) == True

    def test_change_password_and_login_with_old_password(self, client, current_user):
        """Patch to /user/<user_id> url to change to new password, then logging in with old password fails"""
        update_user_url = "/user/" + str(current_user.id)
        res = client.patch(
            update_user_url,
            json={
                "data": {"type": "user", "attributes": {"password": self.new_password}}
            },
        )
        assert res.status_code == 200

        res = client.post(
            "/login", json={"email": current_user.email, "password": "123123"}
        )

        assert res.status_code == 403
