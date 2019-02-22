import os

import jwt
from tests.factories import user


class TestLogin(object):
    """A User can login"""

    def test_root_accessible(self, client, app):
        """Root url is accessible with no login"""
        with app.app_context():
            res = client.get("/")
            assert res.get_data() == b"Greetings User!"

    def test_login_with_email_and_password(self, client, current_user):
        """Post to /login url returns an access token if correct creds and user is confirmed"""

        res = client.post(
            "/login", json={"email": current_user.email, "password": "123123"}
        )

        json_response = res.get_json()

        assert "access_token" in json_response
        assert "refresh_token" in json_response
        assert (
            jwt.decode(json_response["access_token"], os.getenv("JWT_SECRET_KEY"))[
                "identity"
            ]
            == current_user.email
        )

    def test_login_with_unconfirmed_email(self, client):
        """Post to login url with unconfirmed email fails"""
        unconfirmed_user = user.UnconfirmedUserFactory.create()
        res = client.post(
            "/login", json={"email": unconfirmed_user.email, "password": "123123"}
        )

        assert res.status_code == 403

    def test_login_with_wrong_email(self, client):
        """Post to login url with wrong email fails"""

        res = client.post(
            "/login", json={"email": "bob@wehadababyitsaboy.com", "password": "123123"}
        )

        assert res.status_code == 403

    def test_login_with_wrong_password(self, client, current_user):
        """Post to login url with wrong password fails in same way"""

        res = client.post(
            "/login",
            json={"email": current_user.email, "password": "definitely-not-it"},
        )

        assert res.status_code == 403

    def test_session_with_refresh_token(self, refresh_client, current_user):
        """Put to session refresh url with refresh token"""

        res = refresh_client.put("/session")

        assert res.status_code == 200
