from tests.factories.user import (
    UnconfirmedUserFactory,
    UserFactory,
    UnstripedUserFactory,
    StripedUserFactory,
)
from app.models import User, Subdomain, Tunnel, AsyncJob
from tests.factories import subdomain, tunnel
from tests.support.client import TestClient
from unittest import mock
from app.services import authentication
from app.models import Plan
from app import stripe
from tests.support.assertions import assert_valid_schema
import re
import jwt
import pytest


class TestAccount(object):
    @mock.patch("app.services.user.user_notification.send_confirm_email.queue")
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
        assert send_confirm_email.call_count == 2
        (email, token), _ = send_confirm_email.call_args
        assert email == "forgetful@gmail.com"
        assert re.match("http://localhost:5000/account/confirm(.*)", token)

    @mock.patch(
        "app.services.user.user_notification.send_password_reset_confirm_email.queue"
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
        "app.services.user.user_notification.send_password_reset_confirm_email.queue"
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

    @mock.patch("app.services.user.user_notification.send_confirm_email.queue")
    def test_register_with_existing_account_no_email_sent(
        self, send_confirm_email, unauthenticated_client, session
    ):
        """Attempting to register with an already existing account should not
        send an email confirm email"""

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

    @mock.patch("app.services.user.user_notification.send_confirm_email.queue")
    def test_email_confirm_token_with_non_existing_account_no_email_sent(
        self, send_confirm_email, unauthenticated_client, session
    ):
        """Attempting to request a email confirm token with an email that is
        not registered yet should not send an email"""

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
        "app.services.user.user_notification.send_password_reset_confirm_email.queue"
    )
    def test_password_reset_token_with_non_existing_account_no_email_sent(
        self, send_password_reset_confirm_email, unauthenticated_client, session
    ):
        """Attempting to request a password reset token with an email that is
        not registered yet should not send an email"""

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
        "app.services.user.user_notification.send_password_change_confirm_email.queue"
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

        user = User.query.filter_by(email=current_user.email).first_or_404()
        assert res.status_code == 200
        assert user.check_password("abc123") is True
        password_changed_email.assert_called_once()

    @mock.patch(
        "app.services.user.user_notification.send_password_change_confirm_email.queue"
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
        "app.services.user.user_notification.send_email_change_confirm_email.queue"
    )
    def test_change_email_with_correct_credentials(
        self, email_changed_email, client, current_user
    ):
        """PATCH to /account url with correct email succeeds and old email gets
        confirmation"""

        old_email = current_user.email
        new_email = "fresh-email@gmail.com"

        res = client.patch(
            "/account",
            json={"data": {"type": "user", "attributes": {"email": new_email}}},
        )

        old_email_user = User.query.filter_by(email=old_email).first()
        new_email_user = User.query.filter_by(email=new_email).first()
        assert res.status_code == 200
        assert old_email_user is None
        assert new_email_user is not None

        email_changed_email.assert_called_once_with(old_email)

    @mock.patch(
        "app.services.user.user_notification.send_email_change_confirm_email.queue"
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
        res = client.delete(
            "/account",
            json={"data": {"type": "user", "attributes": {"password": "123123"}}},
        )
        user = User.query.filter_by(uuid=current_user.uuid).first()

        assert res.status_code is 200
        assert user is None

    def test_account_delete_account_with_reserved_subdomains(
        self, client, current_user, session
    ):
        """DELETE to /account url succeeds and associated reserved subdomains
        no longer exists"""
        sub1 = subdomain.ReservedSubdomainFactory(user=current_user, name="sub-bass")
        session.add(sub1)
        session.flush()

        assert Subdomain.query.filter_by(id=sub1.id).first() is not None

        res = client.delete(
            "/account",
            json={"data": {"type": "user", "attributes": {"password": "123123"}}},
        )

        assert res.status_code is 200
        assert User.query.filter_by(uuid=current_user.uuid).first() is None
        assert Subdomain.query.filter_by(id=sub1.id).first() is None

    def test_account_delete_account_with_existing_tunnels(
        self, client, current_user, session
    ):
        """DELETE to /account url succeeds and associated tunnels no longer exists"""
        sub1 = subdomain.ReservedSubdomainFactory(user=current_user, name="supersub")
        tun1 = tunnel.TunnelFactory(subdomain=sub1)

        session.add(tun1)
        session.flush()

        assert Subdomain.query.filter_by(id=sub1.id).first() is not None
        assert Tunnel.query.filter_by(job_id=tun1.job_id).first() is not None

        res = client.delete(
            "/account",
            json={"data": {"type": "user", "attributes": {"password": "123123"}}},
        )

        assert res.status_code is 200
        assert User.query.filter_by(uuid=current_user.uuid).first() is None
        assert Subdomain.query.filter_by(id=sub1.id).first() is None
        assert Tunnel.query.filter_by(job_id=tun1.job_id).first() is None

    def test_revoke_tokens(self, app, current_user, client, unauthenticated_client):
        """Delete to /account/token url returns a 204 on success and bearer
        token no longer works"""
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

    def test_returns_an_403_when_using_old_user_uuid(self, current_user, client):
        """Returns an access denied when old uuid is used in token"""
        token = authentication.encode_token(current_user.email, "password-reset")
        client.delete("/account/token")
        res = client.get(f"/account/confirm/{token}")

        assert res.status_code == 403

    def test_get_user(self, current_user, client):
        """Returns an access denied when old uuid is used in token"""
        res = client.get("/account")
        assert_valid_schema(res.get_data(), "user.json")

    @pytest.mark.vcr()
    def test_user_can_update_payment_method_with_customer_id(
        self, current_free_user, free_client
    ):
        """The user can set a payment method via Stripe Client Side
        when they also set the customer id"""

        # both of these calls happen out of band client side - so
        # we're pretending to be javascript here so we can return these
        # strip ids to the API.
        customer_id = stripe.Customer.create(
            email=current_free_user.email,
            description=f"HP Test User {current_free_user.id}",
        ).id

        pm_id = stripe.PaymentMethod.attach("pm_card_visa", customer=customer_id).id

        res = free_client.patch(
            "/account",
            json={
                "data": {
                    "type": "user",
                    "attributes": {
                        "stripe_payment_method": pm_id,
                        "stripe_id": customer_id,
                    },
                }
            },
        )

        assert res.status_code == 200

        user = User.query.filter_by(uuid=current_free_user.uuid).first()
        assert user.stripe_payment_method == pm_id
        assert user.stripe_id == customer_id

    def test_user_cannot_set_payment_id_without_cus_id(self, current_user, client):
        """ The user cannot set a payment method without sending the customer id """

        res = client.patch(
            "/account",
            json={
                "data": {
                    "type": "user",
                    "attributes": {"stripe_payment_method": "pm_works"},
                }
            },
        )

        assert res.status_code == 400

    def test_user_can_set_cust_id_without_payment(self, app, session):
        """ The user can set their cust_id without a payment"""

        app.test_client_class = TestClient
        unstriped_user = UnstripedUserFactory()
        session.add(unstriped_user)
        session.flush()
        with app.test_client(user=unstriped_user) as client:
            res = client.patch(
                "/account",
                json={
                    "data": {"type": "user", "attributes": {"stripe_id": "cust_12345"}}
                },
            )

            assert res.status_code == 200
            user = User.query.filter_by(uuid=unstriped_user.uuid).first()
            assert user.stripe_payment_method is None
            assert user.stripe_id == "cust_12345"

    def test_unstriped_user_cannot_modify_plan(self, app, session):
        """ The user can update plan id only if paymenet method and customer id
        are set. They cannot be set in the same request."""

        app.test_client_class = TestClient
        user = UnstripedUserFactory()
        session.add(user)
        session.flush()
        plan_id = Plan.paid().id
        with app.test_client(user=user) as client:
            res = client.patch(
                "/account",
                json={
                    "data": {
                        "type": "user",
                        "relationships": {
                            "plan": {"data": {"type": "plan", "id": str(plan_id)}}
                        },
                    }
                },
            )

        assert res.status_code == 422

    @pytest.mark.vcr()
    def test_striped_user_can_modify_plan(self, app, session):
        """ A user with a valid stripe_id is able to change their payment method """

        app.test_client_class = TestClient
        user = StripedUserFactory(tier="free", stripe__payment_method="pm_card_visa")
        session.add(user)
        session.flush()
        plan_id = Plan.paid().id

        with app.test_client(user=user) as client:
            res = client.patch(
                "/account",
                json={
                    "data": {
                        "type": "user",
                        "attributes": {},
                        "relationships": {
                            "plan": {"data": {"type": "plan", "id": str(plan_id)}}
                        },
                    }
                },
            )

            assert res.status_code == 200
            user = User.query.filter_by(uuid=user.uuid).first()
            assert user.tier == "paid"

    @mock.patch("app.jobs.payment.user_async_subscribe")
    @mock.patch("app.jobs.payment.user_async_unsubscribe")
    def test_web_hooks_available_only_to_stripe(
        self, async_subscribe, async_unsubscribe, unauthenticated_client
    ):

        res = unauthenticated_client.post(
            "/account/hook",
            json={"data": {"event": {"type": "invoice.payment_suceeded"}}},
        )

        assert not async_subscribe.called
        assert not async_unsubscribe.called
        assert res.status_code == 403

    @mock.patch(
        "app.jobs.payment.user_async_subscribe.queue", return_value=AsyncJob(id=1)
    )
    @mock.patch(
        "app.jobs.payment.user_async_unsubscribe.queue", return_value=AsyncJob(id=1)
    )
    def test_async_subscription_create_changes_a_users_plan(
        self, async_unsubscribe, async_subscribe, unauthenticated_client, stripe_event
    ):
        signature, payload = stripe_event(
            {"type": "invoice.payment_suceeded", "data": {"object": "event"}}
        )
        res = unauthenticated_client.post(
            "/account/hook", headers={"stripe-signature": signature}, data=payload
        )

        assert async_subscribe.called_once
        assert not async_unsubscribe.called
        assert res.status_code == 202

    @mock.patch(
        "app.jobs.payment.user_async_subscribe.queue", return_value=AsyncJob(id=1)
    )
    @mock.patch(
        "app.jobs.payment.user_async_unsubscribe.queue", return_value=AsyncJob(id=1)
    )
    def test_async_subscription_cancel_changes_a_users_plan(
        self, async_unsubscribe, async_subscribe, unauthenticated_client, stripe_event
    ):
        signature, payload = stripe_event(
            {"type": "invoice.payment_failed", "data": {"object": "event"}}
        )

        res = unauthenticated_client.post(
            "/account/hook", headers={"stripe-signature": signature}, data=payload
        )

        assert async_unsubscribe.called_once
        assert not async_subscribe.called
        assert res.status_code == 202
