from flask import request, jsonify, Blueprint, redirect, current_app
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_refresh_token_required,
)
from app import db
from app.services import authentication
from app.models import User
from app.serializers import ErrorSchema
from app.utils.errors import (
    BadRequest,
    AccessDenied,
    UnprocessableEntity,
    UserNotConfirmed,
)
from app.utils.json import json_api
from sqlalchemy.exc import IntegrityError

auth_blueprint = Blueprint("auth", __name__)


@auth_blueprint.route("/")
@auth_blueprint.route("/index")
def index():
    return "Greetings User!"


@auth_blueprint.route("/health_check")
def health_check():
    return "OK"


@auth_blueprint.route("/login", methods=["POST"])
def login():
    if not request.is_json:
        return json_api(BadRequest, ErrorSchema), 400

    email = request.json.get("email", None)
    password = request.json.get("password", None)
    if not (email and password):
        return json_api(BadRequest, ErrorSchema), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return json_api(AccessDenied, ErrorSchema), 403
    if not user.confirmed:
        return json_api(UserNotConfirmed, ErrorSchema), 403
    if not user.check_password(password):
        return json_api(AccessDenied, ErrorSchema), 403
    access_token = create_access_token(identity=email)
    refresh_token = create_refresh_token(identity=email)
    ret = {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires-in": 3600,
        "refresh_token": refresh_token,
    }
    return jsonify(ret), 200


@auth_blueprint.route("/session", methods=["PUT"])
@jwt_refresh_token_required
def session():
    current_user = get_jwt_identity()
    ret = {
        "access_token": create_access_token(identity=current_user),
        "token_type": "Bearer",
        "expires-in": 3600,
    }
    return jsonify(ret), 200


@auth_blueprint.route("/user", methods=["POST"])
def register_user():
    if not request.is_json:
        return json_api(BadRequest, ErrorSchema), 400

    email = request.json.get("email", None)
    password = request.json.get("password", None)

    if not email and password:
        return json_api(BadRequest, ErrorSchema), 400

    newuser = User(email=email, confirmed=False, tier="free")

    try:
        newuser.set_password(password)
        db.session.add(newuser)
        db.session.flush()
        authentication.send_registration_email(email)
    except IntegrityError:
        return json_api(UnprocessableEntity, ErrorSchema), 422
    return "", 204


@auth_blueprint.route("/resend", methods=["POST"])
def resend_confirm_email():
    if not request.is_json:
        return json_api(BadRequest, ErrorSchema), 400

    email = request.json.get("email", None)

    if not (email):
        return json_api(BadRequest, ErrorSchema), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return "", 204
    if user.confirmed:
        return "", 204
    authentication.send_registration_email(email)
    return "", 204


@auth_blueprint.route("/confirm/<token>", methods=["GET"])
def confirm_user(token):
    email = authentication.decode_token(token)
    if not email:
        return redirect("https://holepunch.io/bad_token/")
    user = User.query.filter_by(email=email).first_or_404()
    if user.confirmed:
        return redirect("https://holepunch.io/login")
    user.confirmed = True
    db.session.add(user)
    db.session.flush()
    return redirect("https://holepunch.io/email_confirmed/")
