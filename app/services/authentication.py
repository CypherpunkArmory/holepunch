from itsdangerous import URLSafeTimedSerializer, BadSignature
from flask import current_app, request
from app import stripe
from functools import wraps
from flask_jwt_extended import get_jwt_claims
from app.utils.errors import AccessDenied, BadRequest
from app.utils.json import json_api
from app.serializers import ErrorSchema


def encode_token(uuid, salt="default-salt"):
    serializer = URLSafeTimedSerializer(current_app.config["JWT_SECRET_KEY"])
    return serializer.dumps(str(uuid), salt)


def decode_token(token, salt="default-salt", expiration=3600):
    serializer = URLSafeTimedSerializer(current_app.config["JWT_SECRET_KEY"])
    try:
        return serializer.loads(token, salt=salt, max_age=expiration)
    except BadSignature:
        return False


def jwt_scope_required(**required_scopes):
    def decorator_jwt_scope_required(func):
        @wraps(func)
        def wrapper_jwt_scope_required(*args, **kwargs):
            scopes = jwt_scopes()
            # JWT scopes intersect with the allows scopes
            if "any_of" in required_scopes and not (
                set(required_scopes["any_of"]) & scopes
            ):
                raise AccessDenied("Insuffient scope")

            # Allowed claims are a proper subset of jwt scopes
            if "all_of" in required_scopes and not (
                set(required_scopes["all_of"]) <= scopes
            ):
                raise AccessDenied("Insuffient scope")

            return func(*args, **kwargs)

        return wrapper_jwt_scope_required

    return decorator_jwt_scope_required


def stripe_webhook(func):
    @wraps(func)
    def stripe_webhook_wrapper(*args, **kwargs):
        payload = request.data.decode("utf-8")

        try:
            sig_header = request.headers["stripe-signature"]
            event = stripe.Webhook.construct_event(
                payload, sig_header, current_app.config["STRIPE_ENDPOINT_SECRET"]
            )
        except ValueError:
            # Invalid JSON
            return json_api(BadRequest(), ErrorSchema), 400
        except (KeyError, stripe.error.SignatureVerificationError):
            return json_api(AccessDenied(), ErrorSchema), 403

        return func(event=event, *args, **kwargs)

    return stripe_webhook_wrapper


def validate_scope_permissions(parent_scope, scopes, attrs):
    if parent_scope in scopes:
        return

    allowed_attrs = set(scope.split(":")[-1] for scope in scopes)

    # if the allowed_keys do not include all of the requested keys,
    # throw an error
    if not allowed_attrs >= set(attrs.keys()):
        disallowed = set(attrs.keys()) - scopes
        raise AccessDenied(source=f"{disallowed} is not in allowed scopes")


# TODO cache the results of this call since it's O(n) over scopes
def jwt_scopes():
    return set(get_jwt_claims().get("scopes", []))
