from app.models import User
from app.jobs.email import (
    send_beta_backlog_notification_email,
    send_confirm_email,
    send_password_change_confirm_email,
    send_password_reset_confirm_email,
    send_email_change_confirm_email,
)
from app.services.authentication import encode_token
from flask import current_app


class UserNotification:
    def __init__(self, user: User):
        self.user = user

    def activation_emails(self):
        if self.user.confirmed:
            return

        if self.user.tier() == "waiting":
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
        return current_app.config["CONFIRM_URL"].format(token)
