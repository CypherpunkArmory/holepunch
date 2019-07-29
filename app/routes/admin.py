"""
Provides CRUD operations for Tunnel Resources
"""

from flask import Blueprint, request, Response, make_response
from flask_jwt_extended import get_jwt_identity, jwt_required
from app import json_schema_manager, logger
from app.models import Tunnel, User, Subdomain
from app.serializers import ErrorSchema
from app.services.tunnel import TunnelDeletionService
from app.utils.errors import NotFoundError, TunnelError, BadRequest
from app.utils.json import dig, json_api
from typing import Tuple
from jsonschema import ValidationError

admin_blueprint = Blueprint("admin", __name__)


@admin_blueprint.route("/admin/tunnels", methods=["POST"])
@jwt_required
def tunnel_admin() -> Tuple[Response, int]:
    """
    Stop any currently running tunnel if you are an admin
    """
    current_user = User.query.filter_by(uuid=get_jwt_identity()).first_or_404()
    if current_user.tier() != "admin":
        return json_api(NotFoundError, ErrorSchema), 404

    try:
        json_schema_manager.validate(request.json, "admin_tunnel.json")

        subdomain_name = dig(request.json, "data/attributes/subdomainName")
        reason = dig(request.json, "data/attributes/reason")
    except ValidationError as e:
        return json_api(BadRequest(source=e.message), ErrorSchema), 400

    subdomain = Subdomain.query.filter_by(name=subdomain_name).first_or_404()
    tunnel = Tunnel.query.filter_by(subdomain_id=subdomain.id).first_or_404()
    try:
        TunnelDeletionService(current_user, tunnel).delete()
        logger.info(
            "%s deleted %s.holepunch.io for reason %s",
            current_user.email,
            subdomain_name,
            reason,
        )
        return make_response(""), 204
    except TunnelError:
        return json_api(TunnelError, ErrorSchema), 500
