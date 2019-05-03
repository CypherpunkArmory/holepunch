from app import db
import app.services.authentication as authentication
from app.utils.errors import AccessDenied
from app.services.tunnel import TunnelDeletionService
from app.models import Tunnel


class UserDeletionService:
    def __init__(self, user, **attrs):
        self.user = user
        self.scopes = attrs.pop("scopes")
        authentication.validate_scope_permissions("delete:user", self.scopes, attrs)

    def delete(self):
        if "delete:user" not in self.scopes:
            raise AccessDenied("Insufficient permissions")

        tunnels = Tunnel.query.filter_by(user=self.user)
        for tunnel in tunnels:
            TunnelDeletionService(self.user, tunnel).delete()

        entries_deleted = db.session.delete(self.user)
        db.session.flush()

        return entries_deleted
