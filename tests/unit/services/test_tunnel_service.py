import pytest

from app.services.tunnel import TunnelCreationService
from app.models import UserLimit
from app.jobs.nomad_cleanup import del_tunnel_nomad
from app.utils.errors import TunnelLimitReached
from tests.factories.subdomain import SubdomainFactory, ReservedSubdomainFactory
from unittest.mock import patch
import nomad
from app.utils.dns import discover_service


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
                    port_types=["http"],
                    ssh_key="",
                ).create()

    @pytest.mark.vcr()
    def test_third_invocation_of_named_tunnel_works(self, current_user, session):
        asub = ReservedSubdomainFactory(user=current_user, name="bobjoeboe")
        session.add(asub)
        session.flush()

        first_time = TunnelCreationService(
            current_user=current_user,
            subdomain_id=asub.id,
            port_types=["http"],
            ssh_key="",
        ).create()

        nomad_client = nomad.Nomad(discover_service("nomad").ip)
        del_tunnel_nomad(nomad_client, first_time.job_id)
        asub.in_use = False
        session.add(asub)
        session.flush()

        second_time = TunnelCreationService(
            current_user=current_user,
            subdomain_id=asub.id,
            port_types=["http"],
            ssh_key="",
        ).create()

        nomad_client = nomad.Nomad(discover_service("nomad").ip)
        del_tunnel_nomad(nomad_client, first_time.job_id)
        asub.in_use = False
        session.add(asub)
        session.flush()

        third_time = TunnelCreationService(
            current_user=current_user,
            subdomain_id=asub.id,
            port_types=["http"],
            ssh_key="",
        ).create()

        assert first_time.ssh_port != second_time.ssh_port != third_time.ssh_port
