from app import stripe
from app.models import User, Plan
from app.services.user.user_notification import UserNotification

from app.utils.db import Interactor
from app.utils.errors import UserError
from typing import List, Union, TypeVar, Type, Optional
import stripe.api_resources.list_object

T = TypeVar("T", bound="UserStripe")


class UserStripe(Interactor):
    @classmethod
    def from_customer_id(cls: Type[T], cust_id) -> T:
        user = User.query.filter_by(stripe_id=cust_id).first()
        return cls(user)

    def __init__(self, user: User):
        self.user = user

    @Interactor.flushes("user")
    def create_customer(self) -> bool:
        customer_data = stripe.Customer.create(
            email=self.user.email, description=f"Holepunch User Id: {self.user.id}"
        )
        self.user.stripe_id = customer_data["id"]

        return True

    @Interactor.commits("user")
    def link_to_plan(self, plan: Plan) -> None:
        uns = UserNotification(self.user)
        subscription: stripe.Subscription = None

        # this is an unrecoverable situation - we will need to set
        # up the users stripe id before this point - they should
        # not be able to get here without it.
        assert self.user.stripe_id is not None

        subscription = stripe.Subscription.create(
            customer=self.user.stripe_id,
            default_payment_method=self.user.stripe_payment_method,
            items=[{"plan": plan.stripe_id}],
            expand=["latest_invoice.payment_intent"],
        )

        if subscription.latest_invoice.payment_intent.status == "succeeded":
            uns.subscribed_successfully()
            return

        if subscription.latest_invoice.payment_intent.status == "requires_action":
            uns.subscription_requires_action()
        else:
            uns.subscribed_failed()

        self.user.plan = Plan.free()

    @Interactor.commits("user")
    def unlink_from_plan(self, plan: Plan) -> None:
        uns = UserNotification(self.user)
        subscription: Optional[stripe.Subscription] = None

        subscription = self._retrieve_users_subscriptions(plan)
        if subscription:
            stripe.Subscription.delete(subscription.id, prorate=True)
            uns.unsubscribe_successful(plan.id)
        else:
            uns.unsubscribe_not_required()

    @Interactor.flushes("user")
    def link_to_plan_via_subscription(self, sub_id):
        # This is a "stripe to database" subscription - so we don't need to
        # fire the callbacks that sync stripe
        subscription = stripe.Subscription.retrieve(sub_id, expand=["plan"])
        plan = Plan.query.filter_by(stripe_id=subscription.plan.id).first()
        self.user.plan = plan

    @Interactor.commits("user")
    def unlink_from_plan_via_subscription(self, sub_id):
        # This is a "stripe to database" subscription - so we don't need to
        # fire the callbacks that sync stripe
        stripe.Subscription.delete(sub_id, expand=["plan"])
        self.user.plan = Plan.free()

    def update_stripe_customer(self, updated_field) -> bool:
        if self.user.plan == Plan.free():
            # we don't need to do anything
            return True

        uns = UserNotification(self.user)
        subscription = self._retrieve_users_subscriptions(self.user.plan)
        if subscription:
            if updated_field == "stripe_payment_method":
                stripe.Subscription.modify(
                    subscription.id,
                    default_payment_method=self.user.stripe_payment_method,
                )
                return True
            else:
                uns.unsubscribe_required()
                return False
        else:
            raise UserError(
                detail="User #{user_id} has no subscription and is not on free plan"
            )

    @Interactor.flushes("user")
    def delete_stripe_customer(self) -> bool:
        if self.user.plan != Plan.free():
            self.user.plan = Plan.free()
            self.unlink_from_plan(self.user.plan)

        stripe.Customer.delete(self.user.stripe_id)

        self.user.stripe_id = None
        self.user.stripe_payment_method = None

        return True

    def _retrieve_users_subscriptions(self, plan) -> Optional[stripe.Subscription]:
        subscriptions: Union[stripe.api_resources.list_object.ListObject, List] = []

        subscriptions = stripe.Subscription.list(
            plan=plan.stripe_id, customer=self.user.stripe_id, status="active"
        )

        if len(subscriptions.data) > 1:
            raise UserError(detail="User #{user_id} has multiple active subscriptions")
        elif len(subscriptions.data) == 0:
            return None

        return subscriptions.data[0]
