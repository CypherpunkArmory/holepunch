import pytest

from app.services.tunnel import TunnelCreationService
from app.models import UserLimit
from app.utils.errors import TunnelLimitReached
from tests.factories.subdomain import SubdomainFactory
from unittest.mock import patch


class TestTunnelCreationService(object):
    """Tunnel creation service has correct business logic"""

    def test_create_tunnel_user(self, current_free_user, session):
        """ Raises an exception when too many open tunnels"""

        zero_limit = UserLimit(
            tunnel_count=0, bandwidth=0, forwards=0, reserved_subdomains=0
        )
        asub = SubdomainFactory(user=current_free_user)
        session.add(asub)

        with patch.object(current_free_user, "limits", return_value=zero_limit):
            with pytest.raises(TunnelLimitReached):
                TunnelCreationService(
                    current_user=current_free_user,
                    subdomain_id=asub.id,
                    port_type=["http"],
                    ssh_key="",
                ).create()
