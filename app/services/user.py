from app import db
from app.models import User, Tunnel
from app.services.tunnel import TunnelDeletionService
from app.utils.errors import UserError, AccessDenied
from sqlalchemy.exc import IntegrityError
from sqlalchemy import event
from flask_jwt_extended import create_access_token
from app.services.authentication import encode_token
from flask import url_for
import uuid

from app.jobs.email import (
    send_beta_backlog_notification_email,
    send_confirm_email,
    send_password_change_confirm_email,
    send_password_reset_confirm_email,
    send_email_change_confirm_email,
)
import app.services.authentication as authentication


class UserNotificationService:
    def __init__(self, user):
        self.user = user

    def activation_emails(self):
        if self.user.confirmed:
            return

        if self.user.tier == "waiting":
            send_beta_backlog_notification_email.queue(self.user.email)
        else:
            self.registration_email()

    def password_reset_email(self):
        if not self.user.confirmed:
            return

        send_password_reset_confirm_email.queue(
            self.user.email, self.generate_confirmation_url("password-reset-salt")
        )

    def password_changed_email(self):
        # Do not send password changed emails to unconfirmed users
        # setting their password for the first time.
        if not self.user.confirmed:
            return

        send_password_change_confirm_email.queue(self.user.email)

    def email_changed_email(self, previous_email):
        if not self.user.confirmed:
            return

        send_email_change_confirm_email.queue(previous_email)

    def registration_email(self):
        send_confirm_email.queue(
            self.user.email, self.generate_confirmation_url("email-confirm-salt")
        )

    def generate_confirmation_url(self, salt):
        token = encode_token(self.user.uuid, salt)
        return url_for("account.confirm", token=token, _external=True)


class UserTokenService:
    def __init__(self, uuid):
        self.uuid = uuid

    def confirm(self):
        user = User.query.filter_by(uuid=self.uuid).first_or_404()
        user.confirmed = True
        db.session.add(user)
        db.session.flush()

        return True

    def issue_task_token(self, task):
        return create_access_token(identity=self.uuid, user_claims={"scopes": [task]})


class UserCreationService:
    def __init__(self, **attrs):
        self.email = attrs.pop("email")
        self.password = attrs.pop("password")

    def create(self) -> User:
        try:
            new_user = User(
                email=self.email,
                confirmed=False,
                tier=self.get_user_tier(),
                uuid=str(uuid.uuid4()),
            )
            new_user.set_password(self.password)
            db.session.add(new_user)
            db.session.flush()
        except IntegrityError:
            raise UserError(detail="There is already a user with this email")

        return new_user

    def get_user_tier(self) -> str:
        if User.query.filter_by(confirmed=True).count() < 1000:
            return "paid"
        else:
            return "waiting"


class UserUpdateService:
    def __init__(self, user, **attrs):
        self.user = user
        self.scopes = attrs.pop("scopes")
        authentication.validate_scope_permissions("update:user", self.scopes, attrs)
        self.new_password = attrs.pop("new_password", None)
        self.old_password = attrs.pop("old_password", None)
        self.email = attrs.pop("email", None)
        self.attrs = attrs

    def update(self) -> User:
        for attr, val in self.attrs.items():
            setattr(self.user, attr, val)

        # password is special cased because we encrypt it before
        # we actually store it.
        if self.new_password:
            if (
                "update:user:new_password" not in self.scopes
                and not self.user.check_password(self.old_password)
            ):
                raise AccessDenied("Wrong password")
            self.user.set_password(self.new_password)

        elif self.email:
            if User.query.filter_by(email=self.email).first() is not None:
                raise UserError(detail="Email already in use")
            self.user.email = self.email

        db.session.add(self.user)
        db.session.flush()

        return self.user


class UserDeletionService:
    def __init__(self, user, **attrs):
        self.user = user
        self.scopes = attrs.pop("scopes")
        authentication.validate_scope_permissions("delete:user", self.scopes, attrs)

    def delete(self):
        if "delete:user" not in self.scopes:
            raise AccessDenied("Insufficient permissions")

        tunnels = Tunnel.query.filter_by(user=self.user)
        for tunnel in tunnels:
            TunnelDeletionService(self.user, tunnel).delete()

        entries_deleted = db.session.delete(self.user)
        db.session.flush()

        return entries_deleted


@event.listens_for(User.email, "set")
def user_notify_email_change(user, old_value, *_):
    UserNotificationService(user).email_changed_email(old_value)


@event.listens_for(User.password_hash, "set")
def user_notify_password_change(user, *_):
    UserNotificationService(user).password_changed_email()


@event.listens_for(User, "before_insert")
def user_notify_signup(mapper, connect, user):
    UserNotificationService(user).activation_emails()
