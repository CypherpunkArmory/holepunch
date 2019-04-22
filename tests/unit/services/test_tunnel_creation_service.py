import pytest

from app.services.tunnel import TunnelCreationService
from app.utils.errors import TunnelLimitReached


class TestTunnelCreationService(object):
    """Tunnel creation service has correct business logic"""

    def test_create_tunnel(self, current_free_user, current_user):
        """ Raises an exception when too many open tunnels"""
        with pytest.raises(TunnelLimitReached):
            TunnelCreationService(
                current_user=current_free_user,
                subdomain_id=None,
                port_type=["http"],
                ssh_key="",
            ).create()

            TunnelCreationService(
                current_user=current_free_user,
                subdomain_id=None,
                port_type=["http"],
                ssh_key="",
            ).create()

        for x in range(0, 2):
            TunnelCreationService(
                current_user=current_user,
                subdomain_id=None,
                port_type=["http"],
                ssh_key="",
            ).create()

        with pytest.raises(TunnelLimitReached):
            TunnelCreationService(
                current_user=current_user,
                subdomain_id=None,
                port_type=["http"],
                ssh_key="",
            ).create()
