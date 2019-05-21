"""
Provides CRUD operations for Tunnel Resources
"""

from flask import Blueprint, request, Response, make_response
from flask_jwt_extended import get_jwt_identity, jwt_required
from jsonschema import ValidationError
from sqlalchemy.orm.exc import NoResultFound

from app import json_schema_manager
from app.models import Tunnel, User, Subdomain
from app.serializers import ErrorSchema, TunnelSchema
from app.services.tunnel import TunnelCreationService, TunnelDeletionService
from app.utils.errors import (
    BadRequest,
    NotFoundError,
    AccessDenied,
    SubdomainInUse,
    SubdomainLimitReached,
    TunnelError,
)
from app.utils.json import dig, json_api
from typing import Tuple


tunnel_blueprint = Blueprint("tunnel", __name__)


@tunnel_blueprint.route("/tunnels", methods=["GET"])
@jwt_required
def tunnel_index() -> Tuple[Response, int]:
    """
    Fetch index of a users current tunnels
    """
    tunnels = User.query.filter_by(uuid=get_jwt_identity()).first_or_404().tunnels

    name = dig(request.query_params, "filter/subdomain/name")
    if name:
        tunnels = tunnels.join(Subdomain).filter(Subdomain.name == name)

    return json_api(tunnels, TunnelSchema, many=True), 200


@tunnel_blueprint.route("/tunnels", methods=["POST"])
@jwt_required
def start_tunnel() -> Tuple[Response, int]:
    try:
        json_schema_manager.validate(request.json, "tunnel_create.json")

        subdomain_id = dig(request.json, "data/relationships/subdomain/data/id")
        port_type = dig(request.json, "data/attributes/port")
        ssh_key = dig(request.json, "data/attributes/sshKey")

        current_user = User.query.filter_by(uuid=get_jwt_identity()).first_or_404()
        try:
            tunnel_info = TunnelCreationService(
                current_user, subdomain_id, port_type, ssh_key
            ).create()
        except SubdomainLimitReached:
            return json_api(SubdomainLimitReached, ErrorSchema), 403
        except TunnelError:
            return json_api(TunnelError, ErrorSchema), 500

        return json_api(tunnel_info, TunnelSchema), 201

    except ValidationError as e:
        return json_api(BadRequest(detail=e.message), ErrorSchema), 400

    except AccessDenied:
        return json_api(AccessDenied, ErrorSchema), 403

    except SubdomainInUse:
        return json_api(SubdomainInUse, ErrorSchema), 403


@tunnel_blueprint.route("/tunnels/<int:tunnel_id>", methods=["DELETE"])
@jwt_required
def stop_tunnel(tunnel_id) -> Tuple[Response, int]:
    """
    Stop a currently running tunnel
    """
    if not tunnel_id:
        return json_api(BadRequest, ErrorSchema), 400

    current_user = User.query.filter_by(uuid=get_jwt_identity()).first_or_404()
    tunnel = Tunnel.query.filter_by(user=current_user, id=tunnel_id).first_or_404()

    try:
        TunnelDeletionService(current_user, tunnel).delete()
        return make_response(""), 204
    except NoResultFound:
        return json_api(NotFoundError, ErrorSchema), 404
    except TunnelError:
        return json_api(TunnelError, ErrorSchema), 500


@tunnel_blueprint.route("/tunnels/<int:tunnel_id>", methods=["GET"])
@jwt_required
def get_tunnel(tunnel_id) -> Tuple[Response, int]:
    """
    Retrieve Tunnel Resource
    """
    if not tunnel_id:
        return json_api(BadRequest, ErrorSchema), 400

    current_user = User.query.filter_by(uuid=get_jwt_identity()).first_or_404()
    tunnel = Tunnel.query.filter_by(user=current_user, id=tunnel_id).first_or_404()

    try:
        return json_api(tunnel, TunnelSchema), 200
    except NoResultFound:
        return json_api(NotFoundError, ErrorSchema), 404
