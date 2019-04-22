from tests.factories.user import UnconfirmedUserFactory, UserFactory
from app.models import User
from unittest import mock
from app.services import authentication
import re
import jwt
import os


class TestAccount(object):
    @mock.patch("app.services.user.send_confirm_email.queue")
    def test_obtain_email_confirm_token(
        self, send_confirm_email, unauthenticated_client, session
    ):
        """Send a email confirm token via email"""
        user = UnconfirmedUserFactory(email="forgetful@gmail.com")
        session.add(user)
        session.flush()

        res = unauthenticated_client.post(
            "/account/token",
            json={
                "data": {
                    "type": "email_confirm",
                    "attributes": {"email": "forgetful@gmail.com"},
                }
            },
        )

        assert res.status_code == 200
        send_confirm_email.assert_called_once()
        (email, token), _ = send_confirm_email.call_args
        assert email == "forgetful@gmail.com"
        assert re.match("http://localhost:5000/account/confirm(.*)", token)

    @mock.patch("app.services.user.send_password_reset_confirm_email.queue")
    def test_obtain_a_password_reset_token(
        self, password_reset_email, unauthenticated_client, session
    ):
        """Sends a password reset token via email"""
        user = UserFactory(email="forgetful@gmail.com")
        session.add(user)
        session.flush()

        res = unauthenticated_client.post(
            "/account/token",
            json={
                "data": {
                    "type": "password_reset",
                    "attributes": {"email": "forgetful@gmail.com"},
                }
            },
        )

        assert res.status_code == 200
        password_reset_email.assert_called_once()
        (email, token), _ = password_reset_email.call_args
        assert email == "forgetful@gmail.com"
        assert re.match("http://localhost:5000/account/confirm(.*)", token)

    @mock.patch("app.services.user.send_password_reset_confirm_email.queue")
    def test_returns_200_for_non_existent_user(
        self, password_reset_email, unauthenticated_client
    ):
        res = unauthenticated_client.post(
            "/account/token",
            json={
                "data": {
                    "type": "password_reset",
                    "attributes": {"email": "fuzz_you@gmail.com"},
                }
            },
        )

        assert res.status_code == 200
        password_reset_email.assert_not_called()

    def test_returns_an_access_token_when_confirming_a_password_reset_token(
        self, unauthenticated_client
    ):
        """Returns an access_token JWT when confirms a password_reset token """
        token = authentication.encode_token(
            "forgetful@gmail.com", "password-reset-salt"
        )
        res = unauthenticated_client.get(f"/account/confirm/{token}")

        assert res.status_code == 200
        json_response = res.get_json()
        assert "access_token" in json_response
        assert "refresh_token" not in json_response
        assert jwt.decode(json_response["access_token"], os.getenv("JWT_SECRET_KEY"))[
            "user_claims"
        ]["scopes"] == ["update:user:new_password"]

    def test_redirects_to_login_when_confirming_a_email_confirm_token(
        self, unauthenticated_client, session
    ):
        """Returns a redirect to /login when confirming an email-confirm token"""
        user = UnconfirmedUserFactory(email="forgetful@gmail.com")
        session.add(user)
        session.flush()

        token = authentication.encode_token("forgetful@gmail.com", "email-confirm-salt")
        res = unauthenticated_client.get(f"/account/confirm/{token}")

        assert res.status_code == 302
        assert res.headers["Location"] == "http://localhost:5000/session"

    def test_register_with_email_and_password(self, unauthenticated_client):
        """Post to /account url returns a 204 on success"""

        res = unauthenticated_client.post(
            "/account",
            json={
                "data": {
                    "type": "user",
                    "attributes": {
                        "email": "testing@example.com",
                        "password": "123123",
                    },
                }
            },
        )

        assert res.status_code == 204

    def test_register_with_taken_email(self, unauthenticated_client, session):
        """Post to register url with taken email fails"""

        user = UserFactory(email="test@example.com")
        session.add(user)
        session.flush()

        res = unauthenticated_client.post(
            "/account",
            json={
                "data": {
                    "type": "user",
                    "attributes": {"email": "test@example.com", "password": "123123"},
                }
            },
        )

        assert res.status_code == 422

    @mock.patch("app.services.user.send_password_change_confirm_email.queue")
    def test_change_password_with_correct_credentials(
        self, password_changed_email, client, current_user
    ):
        """PATCH to /account url with correct credentials succeeds"""

        assert current_user.check_password("123123") is True
        res = client.patch(
            "/account",
            json={
                "data": {
                    "type": "user",
                    "attributes": {"old_password": "123123", "new_password": "abc123"},
                }
            },
        )

        user = User.query.filter_by(email=current_user.email).first()
        assert res.status_code == 200
        assert user.check_password("abc123") is True
        password_changed_email.assert_called_once()

    @mock.patch("app.services.user.send_password_change_confirm_email.queue")
    def test_change_password_with_incorrect_password(
        self, password_changed_email, client, current_user
    ):
        """PATCH to /account url with incorrect password fails"""

        res = client.patch(
            "/account",
            json={
                "data": {
                    "type": "user",
                    "attributes": {
                        "old_password": "definitely-wrong",
                        "new_password": "abc123",
                    },
                }
            },
        )

        user = User.query.filter_by(email=current_user.email).first()
        assert res.status_code == 403
        assert user.check_password("abc123") is False
        password_changed_email.assert_not_called()
