from sqlalchemy import event
from app.models import User
from app.services.user.user_notification_service import UserNotificationService
from typing import NamedTuple


class UserLimit(NamedTuple):
    tunnel_count: int
    bandwidth: int
    forwards: int


LIMITS = {
    "free": {"tunnel_count": 1, "bandwidth": 100, "forwards": 2},
    "paid": {"tunnel_count": 5, "bandwidth": 100000, "forwards": 9999},
    "beta": {"tunnel_count": 2, "bandwidth": 1000, "forwards": 10},
}


def get_user_limits(tier: str) -> UserLimit:
    return UserLimit(**(LIMITS[tier]))


@event.listens_for(User.password_hash, "set")
def user_notify_password_change(user, *_):
    UserNotificationService(user).password_changed_email()


@event.listens_for(User, "before_insert")
def user_notify_signup(mapper, connect, user):
    UserNotificationService(user).activation_emails()


@event.listens_for(User.email, "set")
def user_notify_email_change(user, old_value, *_):
    UserNotificationService(user).email_changed_email(old_value)
