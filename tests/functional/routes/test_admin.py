from tests.factories import subdomain
from app.services.tunnel import TunnelCreationService
import pytest


class TestAdmin(object):
    """Logged in Users can manage their tunnels"""

    def test_non_admin_404(self, client):
        """Correct response for empty tunnel list"""
        res = client.post("/admin/tunnel")
        assert res.status_code == 404

    @pytest.mark.vcr()
    def test_tunnel_index(self, admin_client, current_user, session):
        """User can list all of their tunnels"""
        sub = subdomain.ReservedSubdomainFactory(
            user=current_user, name="testtunnelsubdomain"
        )
        session.add(sub)
        session.flush()
        tun = TunnelCreationService(
            current_user, sub.id, ["http"], "i-am-a-lousy-key"
        ).create()
        session.add(tun)
        session.flush()

        res = admin_client.post(
            "/admin/tunnels",
            json={
                "data": {
                    "type": "tunnel",
                    "attributes": {
                        "subdomainName": "testtunnelsubdomain",
                        "reason": "testing",
                    },
                }
            },
        )
        assert res.status_code == 204
