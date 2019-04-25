from itsdangerous import URLSafeTimedSerializer, BadSignature
from flask import current_app
from functools import wraps
from flask_jwt_extended import get_jwt_claims
from app.utils.errors import AccessDenied


def encode_token(uuid, salt="default-salt"):
    serializer = URLSafeTimedSerializer(current_app.config["JWT_SECRET_KEY"])
    return serializer.dumps(uuid, salt)


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
