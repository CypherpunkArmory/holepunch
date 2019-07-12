from app.jobs.payment import (
    user_async_subscribe,
    user_async_unsubscribe,
    user_subscribed,
    user_unsubscribed,
)

from tests.factories.user import UserFactory
from app.services.user.user_stripe import UserStripe
from unittest import mock
from app.models import Plan
from flask import current_app
import stripe


class TestPaymentJobs(object):
    """Payment jobs retrieve objects from the DB and call the interactors"""

    @mock.patch.object(UserStripe, "link_to_plan", return_value=None)
    def test_user_async_subscribe(self, link_to_plan, session):
        user = UserFactory(tier="free", stripe_id="cust_12345")
        session.add(user)
        session.flush()
        plan = Plan.paid()

        user_subscribed(user.id, plan.id)

        assert link_to_plan.called_once_with(user, plan)

    @mock.patch.object(UserStripe, "unlink_from_plan", return_value=None)
    def test_user_async_unsubscribe(self, unlink_from_plan, session):
        user = UserFactory(tier="free", stripe_id="cust_12345")
        session.add(user)
        session.flush()
        plan = Plan.paid()

        user_unsubscribed(user.id, plan.id)

        assert unlink_from_plan.called_once_with(user, plan)

    @mock.patch.object(UserStripe, "link_to_plan_via_subscription", return_value=None)
    def test_user_subscribed(
        self, link_to_plan_via_subscription, stripe_event, session
    ):
        user = UserFactory(tier="free", stripe_id="cust_12345")
        session.add(user)
        session.flush()

        sig, payload = stripe_event(
            {
                "type": "invoice.payment_suceeded",
                "data": {
                    "object": {
                        "id": "in_1EvALfFWLfbqapoHWcc8UROE",
                        "customer": "cust_12345",
                        "subscription": "sub_FPz9OxlXUE6f5I",
                    }
                },
            }
        )

        event = stripe.Webhook.construct_event(
            payload, sig, current_app.config["STRIPE_ENDPOINT_SECRET"]
        )

        user_async_subscribe(event)

        assert link_to_plan_via_subscription.called_once_with("sub_FPz9OxlXUE6f5I")

    @mock.patch.object(
        UserStripe, "unlink_from_plan_via_subscription", return_value=None
    )
    def test_user_unsubscribed(
        self, unlink_from_plan_via_subscription, stripe_event, session
    ):
        user = UserFactory(tier="free", stripe_id="cust_12345")
        session.add(user)
        session.flush()

        sig, payload = stripe_event(
            {
                "type": "invoice.payment_failed",
                "data": {
                    "object": {
                        "id": "in_1EvALfFWLfbqapoHWcc8UROE",
                        "customer": "cust_12345",
                        "subscription": "sub_FPz9OxlXUE6f5I",
                    }
                },
            }
        )

        event = stripe.Webhook.construct_event(
            payload, sig, current_app.config["STRIPE_ENDPOINT_SECRET"]
        )

        user_async_unsubscribe(event)

        assert unlink_from_plan_via_subscription.called_once_with("sub_FPz9OxlXUE6f5I")
