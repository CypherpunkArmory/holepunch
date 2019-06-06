from sqlalchemy import event
from app.models import User
from app import db
from app.services.user.user_notification import UserNotification
from app.jobs.payment import user_subscribed, user_unsubscribed


@event.listens_for(User.password_hash, "set")
def user_notify_password_change(user, *_):
    UserNotification(user).password_changed_email()


@event.listens_for(User, "before_insert")
def user_notify_signup(mapper, connect, user):
    UserNotification(user).activation_emails()


@event.listens_for(User.email, "set")
def user_notify_email_change(user, old_value, *_):
    UserNotification(user).email_changed_email(old_value)


@event.listens_for(User.plan_id, "set")
def user_tier_change(user, value, oldvalue, initiator):
    if user.plan.name == "paid":

        @event.listens_for(db.session, "after_commit", once=True)
        def subscribe_after_commit(_):
            user_subscribed.queue(user.id, user.plan.id)

    else:

        @event.listens_for(db.session, "after_commit", once=True)
        def unsubscribe_after_commit(_):
            user_unsubscribed.queue(user.id)
