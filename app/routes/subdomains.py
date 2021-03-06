from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from jsonschema import ValidationError

from app import json_schema_manager
from app.models import Subdomain, User
from app.serializers import ErrorSchema, SubdomainSchema
from app.services.subdomain import SubdomainCreationService, SubdomainDeletionService
from app.utils.errors import (
    AccessDenied,
    BadRequest,
    SubdomainError,
    SubdomainTaken,
    SubdomainInUse,
    SubdomainLimitReached,
)
from app.utils.json import dig, json_api

subdomain_blueprint = Blueprint("subdomain", __name__)


@subdomain_blueprint.route("/subdomains", methods=["GET"])
@jwt_required
def subdomain_index():
    subdomains = User.query.filter_by(uuid=get_jwt_identity()).first_or_404().subdomains

    name = dig(request.query_params, "filter/name")
    if name:
        subdomains = subdomains.filter_by(name=name)

    if subdomains:
        return json_api(subdomains, SubdomainSchema, many=True)


@subdomain_blueprint.route("/subdomains", methods=["POST"])
@jwt_required
def subdomain_reserve():
    try:
        json_schema_manager.validate(request.json, "subdomain_create.json")
        current_user = User.query.filter_by(uuid=get_jwt_identity()).first_or_404()
        subdomain = SubdomainCreationService(
            current_user, dig(request.json, "data/attributes/name")
        ).reserve(True)

        return json_api(subdomain, SubdomainSchema), 200
    except ValidationError:
        return (
            json_api(BadRequest(detail="Request does not match schema."), ErrorSchema),
            400,
        )
    except SubdomainLimitReached:
        return json_api(SubdomainLimitReached, ErrorSchema), 403
    except SubdomainTaken:
        return json_api(SubdomainTaken, ErrorSchema), 400
    except SubdomainError:
        return json_api(SubdomainError, ErrorSchema), 500


@subdomain_blueprint.route("/subdomains/<int:subdomain_id>", methods=["DELETE"])
@jwt_required
def subdomain_release(subdomain_id):
    current_user = User.query.filter_by(uuid=get_jwt_identity()).first_or_404()
    subdomain = Subdomain.query.filter_by(
        user=current_user, id=subdomain_id
    ).first_or_404()

    try:
        SubdomainDeletionService(current_user, subdomain).release()
        return "", 204
    except AccessDenied:
        return json_api(BadRequest, ErrorSchema), 403
    except SubdomainInUse:
        return json_api(SubdomainInUse, ErrorSchema), 403


@subdomain_blueprint.route("/subdomains/<int:subdomain_id>", methods=["GET"])
@jwt_required
def get_subdomain(subdomain_id):
    """
    Stop a currently running subdomain
    """
    current_user = User.query.filter_by(uuid=get_jwt_identity()).first_or_404()
    subdomain = Subdomain.query.filter_by(
        user=current_user, id=subdomain_id
    ).first_or_404()

    return json_api(subdomain, SubdomainSchema)
