import pytest
from dpath.util import values
from app.models import Tunnel
from app.services.tunnel import TunnelCreationService, TunnelDeletionService
from app.utils.errors import TunnelError
from tests.factories.user import UserFactory
from tests.factories import subdomain, tunnel
from tests.support.assertions import assert_valid_schema
from unittest import mock
from app import momblish


class TestTunnels(object):
    """Logged in Users can manage their tunnels"""

    def test_empty_tunnel_index(self, client):
        """Correct response for empty tunnel list"""
        res = client.get("/tunnels")
        assert_valid_schema(res.get_json(), "tunnels.json")

    def test_tunnel_index(self, client, current_user, session):
        """User can list all of their tunnels"""
        tun = tunnel.TunnelFactory(subdomain__user=current_user)
        session.add(tun)
        session.flush()

        res3 = client.get("/tunnels")
        assert_valid_schema(res3.get_json(), "tunnels.json")
        assert str(tun.id) in values(res3.get_json(), "data/*/id")

    def test_get_tunnel(self, client, current_user, session):
        """User can get a single tunnel"""
        tun = tunnel.TunnelFactory(subdomain__user=current_user)
        session.add(tun)
        session.flush()

        res3 = client.get(f"/tunnels/{tun.id}")
        assert_valid_schema(res3.get_json(), "tunnel.json")
        assert str(tun.id) in values(res3.get_json(), "data/id")

    def test_get_tunnel_unowned(self, client, current_user, session):
        """User cannot lookup tunnel info that does not belong to them"""
        other_user = UserFactory(email="other_person@gmail.com")
        session.add(other_user)
        session.flush()

        tun = tunnel.TunnelFactory(subdomain__user=other_user)
        session.add(tun)
        session.flush()

        res = client.get(f"/tunnels/{tun.id}")
        assert res.status_code == 404

    @mock.patch.object(momblish, "word", return_value="multipleportssubdomain")
    @pytest.mark.vcr()
    def test_tunnel_open_without_subdomain(
        self, mock_get_unused_subdomain, client, current_user, session
    ):
        """User can open a tunnel without providing a subdomain"""

        res = client.post(
            "/tunnels",
            json={
                "data": {
                    "type": "tunnel",
                    "attributes": {"port": ["http"], "sshKey": "ssh-rsa AAAA\n"},
                }
            },
        )

        assert res.status_code == 201
        assert_valid_schema(res.get_data(), "tunnel.json")
        assert Tunnel.query.filter_by(user=current_user).count() == 1

    @mock.patch.object(momblish, "word", return_value="multipleportssubdomain")
    @pytest.mark.vcr()
    def test_tunnel_open_with_multiple_ports(
        self, mock_get_unused_subdomain, client, current_user, session
    ):
        """User can open a tunnel with multiple ports"""

        res = client.post(
            "/tunnels",
            json={
                "data": {
                    "type": "tunnel",
                    "attributes": {
                        "port": ["tcp", "http", "tcp"],
                        "sshKey": "ssh-rsa AAAA\n",
                    },
                }
            },
        )

        assert res.status_code == 201
        assert_valid_schema(res.get_data(), "tunnel.json")
        assert Tunnel.query.filter_by(user=current_user).count() == 1

    @pytest.mark.vcr()
    def test_tunnel_open_with_subdomain(self, client, current_user, session):
        """User can open a tunnel when providing a subdomain they own"""

        sub = subdomain.ReservedSubdomainFactory(
            user=current_user, name="testtunnelsubdomain"
        )
        session.add(sub)
        session.flush()

        res = client.post(
            "/tunnels",
            json={
                "data": {
                    "type": "tunnel",
                    "attributes": {
                        "port": ["http"],
                        "sshKey": "i-am-a-lousy-public-key",
                    },
                    "relationships": {
                        "subdomain": {"data": {"type": "subdomain", "id": str(sub.id)}}
                    },
                }
            },
        )

        assert res.status_code == 201
        assert len(values(res.get_json(), "data/id")) == 1
        assert_valid_schema(res.get_data(), "tunnel.json")
        assert Tunnel.query.filter_by(user=current_user).count() == 1

    @pytest.mark.vcr()
    def test_tunnel_open_unowned_subdomain(self, client, current_user, session):
        """User can not open a tunnel if they dont own the subdomain"""

        sub = subdomain.ReservedSubdomainFactory(name="unowndedsubdomaintunnel")
        session.add(sub)
        session.flush()

        res = client.post(
            "/tunnels",
            json={
                "data": {
                    "type": "tunnel",
                    "attributes": {"port": ["http"], "sshKey": "i-am-a-lousy-key"},
                    "relationships": {
                        "subdomain": {"data": {"type": "subdomain", "id": str(sub.id)}}
                    },
                }
            },
        )

        assert res.status_code == 403
        assert Tunnel.query.filter_by(user=current_user).count() == 0

    @pytest.mark.vcr()
    def test_tunnel_close_owned(self, client, session, current_user):
        """User can close a tunnel"""

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

        res = client.delete("/tunnels/" + str(tun.id))
        assert res.status_code == 204

    def test_tunnel_close_unowned(self, client):
        """User cant close a tunnel they do not own"""

        # I mean hopefully we're not making 239M subdomains in the test run
        res = client.delete("/tunnel/239402934")

        assert res.status_code == 404

    def test_tunnel_filter_by_subdomain_name(self, client, session, current_user):
        """Can filter a subdomain using JSON-API compliant filters"""

        sub1 = subdomain.ReservedSubdomainFactory(
            user=current_user, name="sub-sandwich"
        )
        sub2 = subdomain.ReservedSubdomainFactory(
            user=current_user, name="subscription"
        )

        tun1 = tunnel.TunnelFactory(subdomain=sub1)
        tun2 = tunnel.TunnelFactory(subdomain=sub2)

        session.add(tun1, tun2)
        session.flush()

        res = client.get(f"/tunnels?filter[subdomain][name]=sub-sandwich")

        assert_valid_schema(res.get_json(), "tunnels.json")
        assert str(tun1.id) in values(res.get_json(), "data/*/id")
        assert str(tun2.id) not in values(res.get_json(), "data/*/id")


class TestFailedTunnels(object):
    @mock.patch.object(
        TunnelCreationService, "create_tunnel_nomad", return_value=("1", [])
    )
    @mock.patch.object(
        TunnelCreationService,
        "get_tunnel_details",
        side_effect=TunnelError(detail="Error"),
        autospec=True,
    )
    @mock.patch.object(TunnelDeletionService, "delete")
    @mock.patch("app.services.tunnel.cleanup_old_nomad_box.queue")
    def test_tunnel_delete_on_fail_deploy(
        self,
        mock_del_tunnel_job,
        mock_del_tunnel_from_db,
        mock_get_tunnel_details,
        mock_create_tunnel,
        client,
        current_user,
    ):
        """Tunnel delete is called when provisioning it fails"""
        res = client.post(
            "/tunnels",
            json={
                "data": {
                    "type": "tunnel",
                    "attributes": {"port": ["http"], "sshKey": "i-am-lousy-public-key"},
                }
            },
        )

        assert res.status_code == 500, res.get_json()
        assert mock_get_tunnel_details.called
        assert not mock_del_tunnel_from_db.called
        assert mock_del_tunnel_job.called

    @mock.patch.object(
        TunnelCreationService,
        "create_tunnel_nomad",
        side_effect=TunnelError(detail="Error"),
        autospec=True,
    )
    @mock.patch.object(TunnelCreationService, "get_tunnel_details")
    @mock.patch.object(TunnelDeletionService, "delete")
    @mock.patch("app.services.tunnel.cleanup_old_nomad_box.queue")
    def test_tunnel_not_delete_on_start_up_fail(
        self,
        mock_del_tunnel_job,
        mock_del_tunnel_from_db,
        mock_get_tunnel_details,
        mock_create_tunnel,
        client,
        current_user,
    ):
        """Tunnel delete is not called when provisioning it fails"""
        res = client.post(
            "/tunnels",
            json={
                "data": {
                    "type": "tunnel",
                    "attributes": {"port": ["http"], "sshKey": "i-am-lousy-public-key"},
                }
            },
        )

        assert res.status_code == 500
        assert mock_create_tunnel.called
        assert not mock_get_tunnel_details.called
        assert not mock_del_tunnel_from_db.called
        assert not mock_del_tunnel_job.called
