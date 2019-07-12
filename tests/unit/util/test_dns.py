import pytest
from app.utils.dns import (
    ServiceSRVRecord,
    ServiceARecord,
    ServiceExplicit,
    discover_service,
)

from collections import Counter
import dns.message
import random
import re

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

A_RESPONSE = """id 29186
opcode QUERY
rcode NOERROR
flags QR RD RA
;QUESTION
nomad. IN A
;ANSWER
nomad. 600 IN A 172.18.0.7
;AUTHORITY
;ADDITIONAL
"""


@pytest.fixture
def response():
    return dns.message.from_text(SRV_RESPONSE)


@pytest.fixture
def a_response():
    return dns.message.from_text(A_RESPONSE)


class TestServiceDiscovery(object):
    def test_service_inits_with_srv_result(self, response):
        """ Service Entries are inited with Service Result"""
        srv = ServiceSRVRecord(response)
        assert srv.url in ["172.31.1.43:4646", "172.31.1.167:4647", "172.31.1.76:4647"]

    def test_service_entry_has_an_ip(self, response):
        """ Service Entry has an IP """
        srv = ServiceSRVRecord(response)
        assert srv.ip in ["172.31.1.43", "172.31.1.167", "172.31.1.76"]

    def test_service_entry_has_a_port(self, response):
        """ Service Entry has a Port"""
        srv = ServiceSRVRecord(response)
        assert srv.port in ["4646", "4647"]

    def test_service_entry_select_by_weights(self, response):
        """ Service Entries are selected by weight when multiple servers share
        a priority"""
        rstate = random.getstate()
        random.seed(5)

        srv = ServiceSRVRecord(response)
        counted = Counter([srv.port for _ in range(100)])
        assert 65 <= counted["4646"] <= 75
        assert 25 <= counted["4647"] <= 35

        random.setstate(rstate)

    def test_service_entry_low_priority_ignored(self, response):
        """ Service Entry low-priority servers are not returned by default"""
        srv = ServiceSRVRecord(response)
        assert "172.31.1.55" not in [x.ip for x in srv.entries()]

    def test_service_discovery_works_locally(self, a_response):
        record = ServiceARecord(a_response)
        assert re.match(r"172.18.0.7", record.ip)

    def test_service_discovery_works_explicity(self, a_response):
        record = ServiceExplicit("nomad")
        assert record.ip == "nomad"

    def test_service_discovery_with_a_record(self):
        ip = discover_service("nomad", "A").ip
        # NOTE - This test depends on the local ip address of your docker bridge
        # which changes from time to time. expand this regex as necessary
        assert re.match(r"172\.1[6789]\.\d{1,3}\.\d{1,3}", ip)
