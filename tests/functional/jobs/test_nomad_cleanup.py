import pytest
from app.jobs.nomad_cleanup import find_unused_boxes
from app.services.tunnel import TunnelCreationService
from tests.factories.subdomain import ReservedSubdomainFactory
import nomad
from app.utils.dns import discover_service


class TestNomadCleanup(object):
    """Nomad Cleanup job kills correct boxes"""

    @pytest.mark.vcr()
    def test_find_unused_boxes(self, current_user, session):
        """ Kills unused boxes """
        asub = ReservedSubdomainFactory(user=current_user, name="bobjoebob")
        session.add(asub)
        session.flush()

        first_time = TunnelCreationService(
            current_user=current_user,
            subdomain_id=asub.id,
            port_types=["http"],
            ssh_key="",
        ).create()
        find_unused_boxes()
        find_unused_boxes()
        nomad_client = nomad.Nomad(discover_service("nomad").ip)
        deploys = nomad_client.job.get_deployments("ssh-client-bobjoebob")
        assert len(deploys) == 0
