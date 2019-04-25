import os

import jwt
from tests.factories import user
from werkzeug.datastructures import Headers
from flask.testing import FlaskClient


class TestAuthentication(object):
    """A User can login"""

    def test_login_with_email_and_password(self, unauthenticated_client, current_user):
        """Post to /login url returns an access token if correct creds and user is confirmed"""

        res = unauthenticated_client.post(
            "/login", json={"email": current_user.email, "password": "123123"}
        )

        json_response = res.get_json()

        assert "access_token" in json_response
        assert "refresh_token" in json_response
        assert (
            jwt.decode(json_response["access_token"], os.getenv("JWT_SECRET_KEY"))[
                "identity"
            ]
            == current_user.uuid
        )

    def test_login_with_unconfirmed_email(self, unauthenticated_client):
        """Post to login url with unconfirmed email fails"""
        unconfirmed_user = user.UnconfirmedUserFactory.create()
        res = unauthenticated_client.post(
            "/login", json={"email": unconfirmed_user.email, "password": "123123"}
        )

        assert res.status_code == 403

    def test_login_with_wrong_email(self, unauthenticated_client):
        """Post to login url with wrong email fails"""

        res = unauthenticated_client.post(
            "/login", json={"email": "bob@wehadababyitsaboy.com", "password": "123123"}
        )

        assert res.status_code == 403

    def test_login_with_wrong_password(self, unauthenticated_client, current_user):
        """Post to login url with wrong password fails in same way"""

        res = unauthenticated_client.post(
            "/login",
            json={"email": current_user.email, "password": "definitely-not-it"},
        )

        assert res.status_code == 403

    def test_session_with_refresh_token(self, refresh_client, current_user):
        """Put to session refresh url with refresh token"""

        res = refresh_client.put("/session")

        assert res.status_code == 200

    def test_login_with_old_calver(self, app, current_user):
        """Login should fail with an old api client"""
        app.test_client_class = FlaskClient
        client = app.test_client()
        api_headers = Headers(
            {"Content-Type": "application/vnd.api+json", "Api-Version": "2000.1.1.0"}
        )
        res = client.post(
            "/login",
            headers=api_headers,
            json={"email": current_user.email, "password": "123123"},
        )
        assert res.status_code == 400

    def test_login_with_malformed_calver(self, app, current_user):
        """Login should fail with a malformed api version"""
        app.test_client_class = FlaskClient
        client = app.test_client()
        api_headers = Headers(
            {"Content-Type": "application/vnd.api+json", "Api-Version": "0.0.0.a"}
        )
        res = client.post(
            "/login",
            headers=api_headers,
            json={"email": current_user.email, "password": "123123"},
        )
        assert res.status_code == 403
