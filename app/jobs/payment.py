from app.models import User, Plan
from app.services.user.user_stripe import UserStripe
from app import Q


@Q.job(func_or_queue="payment", timeout=60000)
def user_subscribed(user_id: int, plan_id: int) -> None:
    plan = Plan.query.get(plan_id)
    user = User.query.get(user_id)
    UserStripe(user).link_to_plan(plan)


@Q.job(func_or_queue="payment", timeout=60000)
def user_unsubscribed(user_id, old_plan_id):
    user = User.query.get(user_id)
    plan = Plan.query.get(old_plan_id)
    UserStripe(user).unlink_from_plan(plan)


@Q.job(func_or_queue="payment", timeout=60000)
def user_async_subscribe(event):
    UserStripe.from_customer_id(
        event.data.object.customer
    ).link_to_plan_via_subscription(event.data.object.subscription)


@Q.job(func_or_queue="payment", timeout=60000)
def user_async_unsubscribe(event):
    UserStripe.from_customer_id(
        event.data.object.customer
    ).unlink_from_plan_via_subscription(event.data.object.subscription)
