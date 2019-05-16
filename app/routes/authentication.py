from flask import request, jsonify, Blueprint
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_refresh_token_required,
)

from app import json_schema_manager, jwt
from app.models import User
from app.serializers import ErrorSchema
from app.utils.errors import BadRequest, AccessDenied, UserNotConfirmed
from app.utils.json import json_api
from jsonschema import ValidationError

auth_blueprint = Blueprint("auth", __name__)


@auth_blueprint.route("/login", methods=["POST"])
@auth_blueprint.route("/session", methods=["POST"])
def login():
    try:
        json_schema_manager.validate(request.json, "login.json")

        email = request.json.get("email", None)
        password = request.json.get("password", None)

        user = User.query.filter_by(email=email).first()

        if not user:
            return json_api(AccessDenied, ErrorSchema), 403
        if not user.confirmed:
            return json_api(UserNotConfirmed, ErrorSchema), 403
        if not user.check_password(password):
            return json_api(AccessDenied, ErrorSchema), 403

        access_token = create_access_token(identity=user.uuid)
        refresh_token = create_refresh_token(identity=user.uuid)
        ret = {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires-in": 3600,
            "refresh_token": refresh_token,
        }

        return jsonify(ret), 200
    except ValidationError:
        return json_api(BadRequest, ErrorSchema), 401


@auth_blueprint.route("/session", methods=["PUT"])
@jwt_refresh_token_required
def session():
    uuid = get_jwt_identity()
    user = User.query.filter_by(uuid=uuid).first()
    if user is None:
        return json_api(AccessDenied, ErrorSchema), 403
    ret = {
        "access_token": create_access_token(identity=uuid),
        "token_type": "Bearer",
        "expires-in": 3600,
    }
    return jsonify(ret), 200


@jwt.user_claims_loader
def ensure_user_claims(email):
    return {"scopes": ["update:user", "delete:user"]}
