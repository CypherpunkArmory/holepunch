from sqlalchemy import event
from app.models import User
from app.services.user.user_notification import UserNotification


@event.listens_for(User, "before_insert")
def user_notify_signup(mapper, connect, user):
    UserNotification(user).activation_emails()
