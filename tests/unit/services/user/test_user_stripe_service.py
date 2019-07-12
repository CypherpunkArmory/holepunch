from tests.factories.user import (
    UserFactory,
    StripedUserFactory,
    UnstripedUserFactory,
    SubscribedUserFactory,
)
from app.services.user.user_stripe import UserStripe
from app.services.user.user_notification import UserNotification
from app.models import Plan
from app import stripe
import pytest
from unittest import mock


class TestUserStripe(object):
    @pytest.mark.vcr()
    def test_create_customer(self):
        """ Create a Stripe Customer for a User """

        # NOTE This is recorded - if you re-record you'll have to modify the stripe_id
        user = UserFactory()
        assert UserStripe(user).create_customer()
        assert user.stripe_id == "cus_FPz8Z3uTNswpjq"

    @pytest.mark.vcr()
    def test_user_from_customer_id(self, session):
        """Create a UserStripe interactor via Stripe Customer ID"""
        user = StripedUserFactory(tier="paid", stripe__payment_method="pm_card_visa")
        session.add(user)
        session.flush()

        uss = UserStripe.from_customer_id(user.stripe_id)

        assert uss.user == user

    @pytest.mark.vcr()
    def test_user_link_to_plan_via_subscription(self):
        """Link a User to a Plan based on a change in their stripe subscription"""
        user = StripedUserFactory(
            tier="paid", stripe__payment_method="pm_card_threeDSecure2Required"
        )

        subscriptions = stripe.Subscription.list(
            plan=Plan.paid().stripe_id, customer=user.stripe_id
        )

        # this subscription is _NOT_ actually paid now, but we check in the event
        # listener - this method just makes sure the User's plan reflects the
        # subscription they'r paying for
        UserStripe(user).link_to_plan_via_subscription(subscriptions.data[0].id)

        assert user.plan == Plan.paid()

    @pytest.mark.vcr()
    def test_user_unlink_from_plan_via_subscription(self):
        """Unlink a User from a plan based on change in their stripe subscription"""
        user = StripedUserFactory(tier="paid", stripe__payment_method="pm_card_visa")
        subscription = UserStripe(user)._retrieve_users_subscriptions(Plan.paid())

        UserStripe(user).unlink_from_plan_via_subscription(subscription.id)

        assert UserStripe(user)._retrieve_users_subscriptions(Plan.paid()) is None
        assert user.plan == Plan.free()

    @mock.patch.object(UserNotification, "unsubscribe_required")
    @pytest.mark.vcr()
    def test_update_customer(
        self, unsubscribe_required, session, attach_payment_method
    ):
        """ Update a Stripe Customers Payment Method Id """
        user = StripedUserFactory(tier="paid", stripe__payment_method="pm_card_visa")
        session.add(user)
        session.flush()

        attach_payment_method(user, "pm_card_mastercard")
        assert UserStripe(user).update_stripe_customer("stripe_payment_method") is True
        assert not unsubscribe_required.called

    @mock.patch.object(UserNotification, "unsubscribe_required")
    @pytest.mark.vcr()
    def test_update_customer_changes_account_id(
        self, unsubscribe_required, session, attach_payment_method
    ):
        """ A user cannot change their stripe id without
        cancelling their subscription first """

        # This is to prevent a refund redirection attack
        # User Alice has an Account
        # Hacker Bob has an Account
        # Hacker Bob gains access to User Alice's account
        # He updates Alice's stripe id to his stripe id
        # He then cancels Alice's subscription, recieving her pro-rated refund

        hacker = StripedUserFactory(
            email="evil@hacker.net",
            tier="paid",
            stripe__payment_method="pm_card_mastercard",
        )
        user = StripedUserFactory(tier="paid", stripe__payment_method="pm_card_visa")
        temp_id = hacker.stripe_id
        hacker.stripe_id = None
        session.add(user)
        session.flush()

        user.stripe_id = temp_id
        assert UserStripe(user).update_stripe_customer("stripe_id") is False
        assert unsubscribe_required.called_once

    @pytest.mark.vcr()
    def test_delete_customer(self, app):
        """ Delete a Stripe Customer """

        user = StripedUserFactory(
            tier="paid", email="delete@me.com", stripe__payment_method="pm_card_visa"
        )
        uss = UserStripe(user)
        uss.link_to_plan(Plan.paid())

        customer_id = user.stripe_id

        UserStripe(user).delete_stripe_customer()

        cus = stripe.Customer.retrieve(customer_id)
        assert cus.deleted is True
        assert user.plan == Plan.free()


@mock.patch.object(UserNotification, "subscription_requires_action")
@mock.patch.object(UserNotification, "subscribed_failed")
@mock.patch.object(UserNotification, "subscribed_successfully")
class TestUserStripeLink(object):
    """ TestUserStrip Subscribe to A Plan """

    @pytest.mark.vcr()
    def test_user_subscribed_successfully(
        self,
        subscribed_successfully,
        subscribed_failed,
        subscription_requires_action,
        session,
    ):
        """ User subscribed sucessfully """
        user = StripedUserFactory(tier="paid", stripe__payment_method="pm_card_visa")
        session.add(user)
        session.flush()
        # the user is a paid user when it is submitted to this job
        # immediately after a commit which changes it's plan_id
        # NOTE: this test does not actually change the user's plan
        UserStripe(user).link_to_plan(user.plan)

        assert not subscribed_failed.called
        assert not subscription_requires_action.called
        assert subscribed_successfully.called_once
        assert user.plan == Plan.paid()

    def test_user_fails_to_subscribe_no_card(self, _sf, _ss, _sfa, session):
        """ User couldn't subscribe because they didn't setup a
            card or stripe account"""
        user = UnstripedUserFactory()
        plan = Plan.paid()
        uss = UserStripe(user)
        session.add(user)
        session.flush()

        with pytest.raises(AssertionError):
            uss.link_to_plan(plan)

    @pytest.mark.vcr()
    def test_user_fails_to_subscribe_decline(
        self,
        subscribed_successfully,
        subscribed_failed,
        subscription_requires_action,
        session,
    ):
        """ User's card was declined when paying """
        # This is the 40000000341 card that will fail when a charge is initiated
        user = StripedUserFactory(
            tier="paid", stripe__payment_method="pm_card_chargeCustomerFail"
        )
        session.add(user)
        session.flush()

        UserStripe(user).link_to_plan(user.plan)

        assert not subscribed_successfully.called
        assert not subscription_requires_action.called
        assert subscribed_failed.called_once
        assert user.plan == Plan.free()

    @pytest.mark.vcr()
    def test_user_fails_to_subscribe_security(
        self,
        subscribed_failed,
        subscribed_successfully,
        subscription_requires_action,
        session,
    ):
        """ User payment failed becaues of additional security
            measures on their account """
        user = StripedUserFactory(
            tier="paid", stripe__payment_method="pm_card_threeDSecure2Required"
        )
        session.add(user)
        session.flush()

        UserStripe(user).link_to_plan(user.plan)

        assert not subscribed_successfully.called
        assert not subscribed_failed.called
        assert subscription_requires_action.called
        assert user.plan == Plan.free()


@mock.patch.object(UserNotification, "unsubscribe_not_required")
@mock.patch.object(UserNotification, "unsubscribe_successful")
class TestUserStripeUnlink(object):
    """ Test Unsubscribed from paid plan """

    @pytest.mark.vcr()
    def test_user_unsubscribed(
        self, unsubscribe_successful, unsubscribe_not_required, session
    ):
        """ User unsubscribes successfully """
        user = SubscribedUserFactory(tier="paid", stripe__payment_method="pm_card_visa")
        user.plan = Plan.free()
        session.add(user)
        session.flush()

        UserStripe(user).unlink_from_plan(Plan.paid())

        assert unsubscribe_successful.called_once
        assert not unsubscribe_not_required.called

    @pytest.mark.vcr()
    def test_user_unsubscribed_but_didnt_need_to(
        self, unsubscribe_successful, unsubscribe_not_required, session
    ):
        """User can't unsubscribe if they're not subscribed in the first place
        <taps forehead>"""

        user = StripedUserFactory(tier="free", stripe__payment_method="pm_card_visa")
        user.plan = Plan.free()
        session.add(user)
        session.flush()

        UserStripe(user).unlink_from_plan(Plan.paid())

        assert not unsubscribe_successful.called
        assert unsubscribe_not_required.called_once
