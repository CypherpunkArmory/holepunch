from itsdangerous import URLSafeTimedSerializer
from flask import current_app, url_for
from app.jobs.email import send_confirm_email


def encode_token(email):
    serializer = URLSafeTimedSerializer(current_app.config["JWT_SECRET_KEY"])
    return serializer.dumps(email, salt="email-confirm-salt")


def decode_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(current_app.config["JWT_SECRET_KEY"])
    try:
        email = serializer.loads(token, salt="email-confirm-salt", max_age=expiration)
        return email
    except Exception as e:
        return False


def generate_registration_url(token):
    return url_for("auth.confirm_user", token=token, _external=True)


def send_registration_email(email_address):
    token = encode_token(email_address)
    confirm_url = generate_registration_url(token)
    send_confirm_email.queue(email_address, confirm_url)
