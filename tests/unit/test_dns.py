import pytest
from app.utils.dns import Service

from collections import Counter
import dns.message

# DO NOT ADJUST THE FORMATTING ON THIS STRING
# IT WILL NOT PARSE

SRV_RESPONSE = """id 26729
opcode QUERY
rcode NOERROR
flags QR AA RD RA
;QUESTION
nomad.service.city.consul. IN SRV
;ANSWER
nomad.service.city.consul. 0 IN SRV 1 70 4646 city1-0114serverless.node.city.consul.
nomad.service.city.consul. 0 IN SRV 1 15 4647 city2-0114serverless.node.city.consul.
nomad.service.city.consul. 0 IN SRV 1 15 4647 city3-0114serverless.node.city.consul.
nomad.service.city.consul. 0 IN SRV 0 15 4647 city4-0114serverless.node.city.consul.
;AUTHORITY
;ADDITIONAL
city1-0114serverless.node.city.consul. 0 IN A 172.31.1.43
city2-0114serverless.node.city.consul. 0 IN A 172.31.1.167
city3-0114serverless.node.city.consul. 0 IN A 172.31.1.76
city4-0114serverless.node.city.consul. 0 IN A 172.31.1.55"""


@pytest.fixture
def response():
    return dns.message.from_text(SRV_RESPONSE)


class TestServiceDiscovery(object):
    def test_service_inits_with_srv_result(self, response):
        """ Service Entries are inited with Service Result"""
        srv = Service(response)
        assert srv.url in ["172.31.1.43:4646", "172.31.1.167:4647", "172.31.1.76:4647"]

    def test_service_entry_has_an_ip(self, response):
        """ Service Entry has an IP """
        srv = Service(response)
        assert srv.ip in ["172.31.1.43", "172.31.1.167", "172.31.1.76"]

    def test_service_entry_has_a_port(self, response):
        """ Service Entry has a Port"""
        srv = Service(response)
        assert srv.port in ["4646", "4647"]

    def test_service_entry_select_by_weights(self, response):
        """ Service Entries are selected by weight when multiple servers share
        a priority"""
        srv = Service(response)
        counted = Counter([srv.port for _ in range(100)])
        assert 65 <= counted["4646"] <= 75
        assert 25 <= counted["4647"] <= 35

    def test_service_entry_low_priority_ignored(self, response):
        """ Service Entry low-priority servers are not returned by default"""
        srv = Service(response)
        assert "172.31.1.55" not in [x.ip for x in srv.entries()]
