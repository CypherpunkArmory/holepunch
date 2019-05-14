from tests.factories.user import UnconfirmedUserFactory, UserFactory
from app.models import User, Subdomain, Tunnel
from tests.factories import subdomain, tunnel
from unittest import mock
from app.services import authentication
import re
import jwt
import requests


class TestAccount(object):
    @mock.patch("app.services.user.user_notification_service.send_confirm_email.queue")
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
        assert send_confirm_email.call_count is 2
        (email, token), _ = send_confirm_email.call_args
        assert email == "forgetful@gmail.com"
        assert re.match("http://localhost:5000/account/confirm(.*)", token)

    @mock.patch(
        "app.services.user.user_notification_service.send_password_reset_confirm_email.queue"
    )
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

    @mock.patch(
        "app.services.user.user_notification_service.send_password_reset_confirm_email.queue"
    )
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
        self, app, unauthenticated_client
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
        assert jwt.decode(json_response["access_token"], app.config["JWT_SECRET_KEY"])[
            "user_claims"
        ]["scopes"] == ["update:user:new_password"]

    def test_correct_status_code_when_confirming_a_email_confirm_token(
        self, unauthenticated_client, session
    ):
        """Returns a redirect to /login when confirming an email-confirm token"""
        user = UnconfirmedUserFactory(email="forgetful@gmail.com")
        session.add(user)
        session.flush()

        token = authentication.encode_token(user.uuid, "email-confirm-salt")
        res = unauthenticated_client.get(f"/account/confirm/{token}")

        assert res.status_code == 204

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

        assert res.status_code == 204, res.get_json()

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

        assert res.status_code == 422, res.get_json()

    @mock.patch("app.services.user.user_notification_service.send_confirm_email.queue")
    def test_register_with_existing_account_no_email_sent(
        self, send_confirm_email, unauthenticated_client, session
    ):
        """Attempting to register with an already existing account should not send an email confirm email"""

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
        send_confirm_email.assert_not_called()

    @mock.patch("app.services.user.user_notification_service.send_confirm_email.queue")
    def test_email_confirm_token_with_non_existing_account_no_email_sent(
        self, send_confirm_email, unauthenticated_client, session
    ):
        """Attempting to request a email confirm token with an email that is not registered yet should not send an email"""

        res = unauthenticated_client.post(
            "/account/token",
            json={
                "data": {
                    "type": "email_confirm",
                    "attributes": {"email": "fake@faker.com"},
                }
            },
        )

        assert res.status_code == 200
        send_confirm_email.assert_not_called()

    @mock.patch(
        "app.services.user.user_notification_service.send_password_reset_confirm_email.queue"
    )
    def test_password_reset_token_with_non_existing_account_no_email_sent(
        self, send_password_reset_confirm_email, unauthenticated_client, session
    ):
        """Attempting to request a password reset token with an email that is not registered yet should not send an email"""

        res = unauthenticated_client.post(
            "/account/token",
            json={
                "data": {
                    "type": "password_reset",
                    "attributes": {"email": "nobody123@noone.com"},
                }
            },
        )

        assert res.status_code == 200
        send_password_reset_confirm_email.assert_not_called()

    @mock.patch(
        "app.services.user.user_notification_service.send_password_change_confirm_email.queue"
    )
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

        user = User.query.filter_by(uuid=current_user.uuid).first_or_404()
        assert res.status_code == 200
        assert user.check_password("abc123") is True
        password_changed_email.assert_called_once()

    @mock.patch(
        "app.services.user.user_notification_service.send_password_change_confirm_email.queue"
    )
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

        user = User.query.filter_by(email=current_user.email).first_or_404()
        assert res.status_code == 403
        assert user.check_password("abc123") is False
        password_changed_email.assert_not_called()

    @mock.patch(
        "app.services.user.user_notification_service.send_email_change_confirm_email.queue"
    )
    def test_change_email_with_correct_credentials(
        self, email_changed_email, client, current_user
    ):
        """PATCH to /account url with correct email succeeds and old email gets confirmation"""
        old_email = current_user.email
        new_email = "fresh-email@gmail.com"

        r = requests.get("http://mail:8025/api/v1/events", stream=True)
        r.encoding = "ascii"

        res = client.patch(
            "/account",
            json={"data": {"type": "user", "attributes": {"email": new_email}}},
        )

        old_email_user = User.query.filter_by(email=old_email).first()
        new_email_user = User.query.filter_by(email=new_email).first()
        assert res.status_code == 200
        assert old_email_user is None
        assert new_email_user is not None

        email_changed_email.assert_called_once()

        for line in r.iter_lines(decode_unicode=True):
            if line and old_email in line:
                r.close()
                break

    @mock.patch(
        "app.services.user.user_notification_service.send_email_change_confirm_email.queue"
    )
    def test_change_email_to_existing_email(
        self, email_changed_email, client, current_user, session
    ):
        """PATCH to /account url with an already existing email fails"""
        other_user = UnconfirmedUserFactory(email="other_guy@gmail.com")
        session.add(other_user)
        session.flush()

        old_email = current_user.email

        res = client.patch(
            "/account",
            json={"data": {"type": "user", "attributes": {"email": other_user.email}}},
        )

        old_email_user = User.query.filter_by(email=old_email).first()
        other_email_user = User.query.filter_by(email=other_user.email).first()
        assert res.status_code == 422
        assert old_email_user is not None
        assert other_email_user is not None

        email_changed_email.assert_not_called()

    def test_account_delete_with_correct_credentials(self, client, current_user):
        """DELETE to /account url succeeds and account no longer exists"""
        res = client.delete("/account")
        user = User.query.filter_by(uuid=current_user.uuid).first()

        assert res.status_code is 200
        assert user is None

    def test_account_delete_account_with_reserved_subdomains(
        self, client, current_user, session
    ):
        """DELETE to /account url succeeds and associated reserved subdomains no longer exists"""
        sub1 = subdomain.ReservedSubdomainFactory(user=current_user, name="sub1")
        session.add(sub1)
        session.flush()

        assert Subdomain.query.filter_by(id=sub1.id).first() is not None

        delete_res = client.delete("/account")

        assert delete_res.status_code is 200
        assert User.query.filter_by(uuid=current_user.uuid).first() is None
        assert Subdomain.query.filter_by(id=sub1.id).first() is None

    def test_account_delete_account_with_existing_tunnels(
        self, client, current_user, session
    ):
        """DELETE to /account url succeeds and associated tunnels no longer exists"""
        sub1 = subdomain.ReservedSubdomainFactory(user=current_user, name="sub1")
        tun1 = tunnel.TunnelFactory(subdomain=sub1)

        session.add(tun1)
        session.flush()

        assert Subdomain.query.filter_by(id=sub1.id).first() is not None
        assert Tunnel.query.filter_by(job_id=tun1.job_id).first() is not None

        res = client.delete("/account")

        assert res.status_code is 200
        assert User.query.filter_by(uuid=current_user.uuid).first() is None
        assert Subdomain.query.filter_by(id=sub1.id).first() is None
        assert Tunnel.query.filter_by(job_id=tun1.job_id).first() is None

    def test_revoke_tokens(self, app, current_user, client, unauthenticated_client):
        """Delete to /account/token url returns a 204 on success and bearer token no longer works"""
        res = unauthenticated_client.post(
            "/login", json={"email": current_user.email, "password": "123123"}
        )

        json_response = res.get_json()

        old_uuid = jwt.decode(
            json_response["access_token"], app.config["JWT_SECRET_KEY"]
        )["identity"]
        res2 = client.delete("/account/token")
        assert res2.status_code == 204

        res3 = client.get("/subdomains")
        assert res3.status_code == 404, res3.get_json()

        res4 = unauthenticated_client.post(
            "/login", json={"email": current_user.email, "password": "123123"}
        )

        json_response = res4.get_json()

        new_uuid = jwt.decode(
            json_response["access_token"], app.config["JWT_SECRET_KEY"]
        )["identity"]
        assert new_uuid != old_uuid
