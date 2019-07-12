from app.services import authentication
from app.services.user.user_creation import UserCreation
from app.services.user.user_update import UserUpdate
from app.services.user.user_deletion import UserDeletion
from app.services.user.user_notification import UserNotification
from app.services.user.user_token import UserToken
from app.models import User
from app.serializers import UserSchema
from flask import request, Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import json_schema_manager
from app.utils.errors import BadRequest, UnprocessableEntity, UserError, AccessDenied
from app.utils.json import json_api, dig
from app.serializers import ErrorSchema
from jsonschema import ValidationError
from werkzeug.exceptions import NotFound
import uuid

account_blueprint = Blueprint("account", __name__)


token_types = ["email-confirm-salt", "password-reset-salt"]


@account_blueprint.route("/account/token", methods=["POST"])
def create_token():
    try:
        json_schema_manager.validate(request.json, "token.json")
        email = dig(request.json, "data/attributes/email", None)
        token_type = dig(request.json, "data/type", None)
        user = User.query.filter_by(email=email).first_or_404()
        uns = UserNotification(user)

        if token_type == "email_confirm":
            uns.activation_emails()
        elif token_type == "password_reset":
            uns.password_reset_email()

    except ValidationError as e:
        return json_api(BadRequest(source=e.message), ErrorSchema), 400
    except NotFound:
        return "", 200

    return "", 200


@account_blueprint.route("/account/confirm/<token>", methods=["GET"])
def confirm(token):
    for salt in token_types:
        uuid = authentication.decode_token(token, salt=salt)
        if salt == "password-reset-salt" and uuid:
            task_token = UserToken(uuid).issue_task_token("update:user:new_password")
            return (
                jsonify(
                    {
                        "access_token": task_token,
                        "token_type": "Bearer",
                        "expires-in": 3600,
                    }
                ),
                200,
            )
        elif salt == "email-confirm-salt" and uuid:
            uuid = authentication.decode_token(token, salt=salt)
            if not UserToken(uuid).confirm():
                return json_api(AccessDenied, ErrorSchema), 403
            return "", 204

    return json_api(AccessDenied, ErrorSchema), 403


@account_blueprint.route("/account/token", methods=["DELETE"])
@jwt_required
@authentication.jwt_scope_required(all_of=["update:user"])
def revoke_all_tokens():
    current_user = User.query.filter_by(uuid=get_jwt_identity()).first_or_404()
    service = UserUpdate(
        current_user,
        scopes=authentication.jwt_scopes(),
        attrs={"uuid": str(uuid.uuid4())},
    )
    service.update()
    return "", 204


@account_blueprint.route("/account", methods=["PATCH"])
@jwt_required
@authentication.jwt_scope_required(any_of=["update:user:new_password", "update:user"])
def update_user():
    """ Update an existing User Record"""

    try:
        json_schema_manager.validate(request.json, "user_update.json")

        current_user = User.query.filter_by(uuid=get_jwt_identity()).first_or_404()

        service = UserUpdate(
            current_user,
            scopes=authentication.jwt_scopes(),
            attrs=dig(request.json, "data/attributes", {}),
            rels=dig(request.json, "data/relationships", {}),
        )
        updated_user = service.update()

        return json_api(updated_user, UserSchema), 200
    except UserError as e:
        return json_api(e, ErrorSchema), 422
    except AccessDenied as e:
        return json_api(e, ErrorSchema), 403
    except ValidationError as e:
        return json_api(BadRequest(source=e.message), ErrorSchema), 400


@account_blueprint.route("/account", methods=["DELETE"])
@jwt_required
@authentication.jwt_scope_required(any_of=["delete:user"])
def delete_user():
    """ Delete an existing User Record"""

    try:
        json_schema_manager.validate(request.json, "user_delete.json")
        current_user = User.query.filter_by(uuid=get_jwt_identity()).first_or_404()

        service = UserDeletion(
            current_user,
            scopes=authentication.jwt_scopes(),
            attrs=dig(request.json, "data/attributes", {}),
        )
        entries_deleted = service.delete()

        return json_api(entries_deleted, UserSchema), 200
    except UserError:
        return json_api(UnprocessableEntity, ErrorSchema), 422
    except AccessDenied as e:
        return json_api(e, ErrorSchema), 403


@account_blueprint.route("/account", methods=["POST"])
def register_user():
    """ Create a new User Record"""
    try:
        json_schema_manager.validate(request.json, "user_create.json")

        user = UserCreation(
            email=dig(request.json, "data/attributes/email"),
            password=dig(request.json, "data/attributes/password"),
        ).create()

        return json_api(user, UserSchema), 204
    except UserError as e:
        return json_api(e, ErrorSchema), 422
    except ValidationError as e:
        return json_api(BadRequest(source=e.message), ErrorSchema), 400


@account_blueprint.route("/account", methods=["GET"])
@jwt_required
def get_user():
    """ Get an existing User Record"""
    current_user = User.query.filter_by(uuid=get_jwt_identity()).first_or_404()
    return json_api(current_user, UserSchema), 200
