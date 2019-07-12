from factory import Factory, post_generation, Faker, lazy_attribute
from pytest_factoryboy import register
import uuid
import string
import datetime

from app.models import User, Plan
from typing import Optional
from secrets import choice
from app import stripe


@register
class UserFactory(Factory):
    class Meta:
        model = User

    class Params:
        tier = "paid"

    email = Faker("email")
    confirmed = True
    stripe_id: Optional[str] = None
    stripe_payment_method: Optional[str] = None

    @post_generation
    def set_password(user, create, extracted, **kwargs):
        user.set_password("123123")

    @post_generation
    def set_uuid(user, create, extracted, **kwargs):
        user.uuid = str(uuid.uuid1())

    @lazy_attribute
    def plan(self):
        return Plan.query.filter_by(name=self.tier).first()

    @lazy_attribute
    def stripe_id(self):
        return "cus_" + "".join(
            [choice(string.ascii_letters + string.digits) for _ in range(8)]
        )

    @lazy_attribute
    def stripe_payment_method(self):
        return "pm_" + "".join(
            [choice(string.ascii_letters + string.digits) for _ in range(8)]
        )


@register
class StripedUserFactory(UserFactory):
    class Params:
        tier = "free"

    email = "user@holepunch.io"

    @post_generation
    def stripe(self, create, extracted, **kwargs):
        customer_id = stripe.Customer.create(
            email=self.email, description=f"HP TEST {datetime.datetime.now()} {self.id}"
        ).id

        self.stripe_id = customer_id

        if kwargs["payment_method"] is None:
            return

        pm_id = stripe.PaymentMethod.attach(
            kwargs["payment_method"], customer=self.stripe_id
        ).id

        self.stripe_payment_method = pm_id


@register
class SubscribedUserFactory(StripedUserFactory):
    @post_generation
    def attach_sub(self, create, extracted, **kwargs):
        stripe.Subscription.create(
            customer=self.stripe_id,
            default_payment_method=self.stripe_payment_method,
            items=[{"plan": self.plan.stripe_id}],
            expand=["latest_invoice.payment_intent"],
        )


@register
class UnstripedUserFactory(UserFactory):
    class Params:
        tier = "free"

    stripe_id = None
    stripe_payment_method = None


@register
class UnconfirmedUserFactory(UserFactory):
    confirmed = False
