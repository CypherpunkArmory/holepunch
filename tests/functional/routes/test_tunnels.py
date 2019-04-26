import pytest
from dpath.util import values
from nomad.api.exceptions import BaseNomadException
from app.models import Tunnel
from app.services.tunnel import TunnelCreationService, TunnelDeletionService
from app.utils.errors import TunnelError
from tests.factories import subdomain, tunnel
from tests.support.assertions import assert_valid_schema
from unittest import mock


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

    @pytest.mark.vcr()
    def test_tunnel_open_without_subdomain(self, client, current_user, session):
        """User can open a tunnel without providing a subdomain"""

        res = client.post(
            "/tunnels",
            json={
                "data": {
                    "type": "tunnel",
                    "attributes": {"port": ["http"], "sshKey": "i-am-lousy-public-key"},
                }
            },
        )

        assert res.status_code == 201
        assert_valid_schema(res.get_data(), "tunnel.json")
        assert Tunnel.query.filter_by(user=current_user).count() == 1

    @pytest.mark.vcr()
    def test_tunnel_open_with_subdomain(self, client, current_user, session):
        """User can open a tunnel when providing a subdomain they own"""

        sub = subdomain.ReservedSubdomainFactory(user=current_user)
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

    def test_tunnel_open_unowned_subdomain(self, client, current_user, session):
        """User can not open a tunnel if they dont own the subdomain"""

        sub = subdomain.ReservedSubdomainFactory()
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

        sub = subdomain.SubdomainFactory(user=current_user)
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
        """User cant close a tunnel they doesnt own"""

        # I mean hopefully we're not making 239M subdomains in the test run
        res = client.delete("/tunnel/239402934")

        assert res.status_code == 404

    def test_tunnel_filter_by_subdomain_name(self, client, session, current_user):
        """Can filter a subdomain using JSON-API compliant filters"""

        sub1 = subdomain.ReservedSubdomainFactory(user=current_user, name="subby-sub")
        sub2 = subdomain.ReservedSubdomainFactory(user=current_user, name="sub-subby")

        tun1 = tunnel.TunnelFactory(subdomain=sub1)
        tun2 = tunnel.TunnelFactory(subdomain=sub2)

        session.add(tun1, tun2)
        session.flush()

        res = client.get(f"/tunnels?filter[subdomain][name]=subby-sub")

        assert_valid_schema(res.get_json(), "tunnels.json")
        assert str(tun1.id) in values(res.get_json(), "data/*/id")
        assert str(tun2.id) not in values(res.get_json(), "data/*/id")

    class TestFailedTunnels(object):
        @mock.patch.object(
            TunnelCreationService,
            "get_tunnel_details",
            side_effect=TunnelError(detail="Error"),
            autospec=True,
        )
        @mock.patch.object(TunnelDeletionService, "del_tunnel_nomad")
        def test_tunnel_delete_on_fail_deploy(
            self, mock_del_tunnel, mock_create_tunnel, client, current_user
        ):
            """Tunnel delete is called when provisioning it fails"""
            res = client.post(
                "/tunnels",
                json={
                    "data": {
                        "type": "tunnel",
                        "attributes": {
                            "port": ["http"],
                            "sshKey": "i-am-lousy-public-key",
                        },
                    }
                },
            )

            assert res.status_code == 500
            assert mock_create_tunnel.called
            assert mock_del_tunnel.called

        @mock.patch.object(
            TunnelCreationService,
            "start_tunnel_nomad",
            side_effect=TunnelError(detail="Error"),
            autospec=True,
        )
        @mock.patch.object(TunnelDeletionService, "del_tunnel_nomad")
        def test_tunnel_not_delete_on_start_up_fail(
            self, mock_del_tunnel, mock_start_tunnel, client, current_user
        ):
            """Tunnel delete is not called when provisioning it fails"""
            res = client.post(
                "/tunnels",
                json={
                    "data": {
                        "type": "tunnel",
                        "attributes": {
                            "port": ["http"],
                            "sshKey": "i-am-lousy-public-key",
                        },
                    }
                },
            )

            assert res.status_code == 500
            assert mock_start_tunnel.called
            assert not mock_del_tunnel.called

        @mock.patch.object(
            TunnelCreationService,
            "start_tunnel_nomad",
            side_effect=BaseNomadException("Error"),
            autospec=True,
        )
        @mock.patch.object(TunnelDeletionService, "del_tunnel_nomad")
        def test_tunnel_nomad_fail(
            self, mock_del_tunnel, mock_start_tunnel, client, current_user
        ):
            """Tunnel delete is not called when nomad fails"""
            res = client.post(
                "/tunnels",
                json={
                    "data": {
                        "type": "tunnel",
                        "attributes": {
                            "port": ["http"],
                            "sshKey": "i-am-lousy-public-key",
                        },
                    }
                },
            )

            assert res.status_code == 500
            assert mock_start_tunnel.called
            assert not mock_del_tunnel.called
