from itsdangerous import URLSafeTimedSerializer, BadSignature
from flask import current_app, url_for
from app.jobs.email import (
    send_beta_backlog_notification_email,
    send_confirm_email,
    send_password_change_confirm_email,
    send_password_reset_confirm_email,
)


def encode_token(email, salt):
    serializer = URLSafeTimedSerializer(current_app.config["JWT_SECRET_KEY"])
    return serializer.dumps(email, salt)


def decode_token(token, salt, expiration=3600):
    serializer = URLSafeTimedSerializer(current_app.config["JWT_SECRET_KEY"])
    try:
        email = serializer.loads(token, salt=salt, max_age=expiration)
        return email
    except BadSignature:
        return False


def generate_registration_url(token):
    return url_for("auth.confirm_user", token=token, _external=True)


def generate_password_reset_url(token, user_id):
    return url_for("auth.update_user", token=token, user_id=user_id, _external=True)


def send_registration_email(email_address):
    token = encode_token(email_address, "email-confirm-salt")
    confirm_url = generate_registration_url(token)
    send_confirm_email.queue(email_address, confirm_url)


def send_password_change_email(email_address):
    send_password_change_confirm_email.queue(email_address)


def send_beta_backlog_email(email_address):
    send_beta_backlog_notification_email.queue(email_address)


def send_password_reset_email(email_address, user_id):
    token = encode_token(email_address, "password-reset-salt")
    reset_url = generate_password_reset_url(token, user_id)
    send_password_reset_confirm_email.queue(email_address, reset_url)
