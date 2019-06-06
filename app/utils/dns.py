import dns.resolver
import dns.name
import dns.rdatatype
import random
import os
from flask import current_app
from functools import lru_cache

from typing import Iterator, NamedTuple, List


class Entry(NamedTuple):
    ip: str
    port: str


class BaseService:
    @staticmethod
    @lru_cache()
    def resolver():
        resolver = dns.resolver.Resolver(configure=False)
        resolver.nameservers = [current_app.config["DNS_ADDR"]]
        resolver.search = [
            dns.name.from_text("service.city.consul"),
            dns.name.from_text("service.consul"),
            dns.name.from_text("."),
        ]

        return resolver

    def __init__(self, response):
        self.response = response
        self.srv: List[Entry] = []
        self.weights: List[int] = []
        self._parse_response()
        self.response_generator = self._response()

    def _parse_response(self) -> None:
        raise NotImplementedError

    def _weighted_choice(self) -> Entry:
        return random.choices(self.srv, self.weights, k=1)[0]

    def _response(self) -> Iterator[Entry]:
        while True:
            yield self._weighted_choice()

    @property
    def url(self) -> str:
        entry = next(self.response_generator)
        return f"{entry.ip}:{entry.port}"

    @property
    def ip(self) -> str:
        return next(self.response_generator).ip

    @property
    def port(self) -> str:
        return next(self.response_generator).port

    def entries(self):
        return self.srv


class ServiceSRVRecord(BaseService):
    def _parse_response(self) -> None:
        """Parse the DNS response into something a little more useful.  PyDNS
        object model is too complicated for everyday use."""

        nodes = {}
        for x in self.response.additional:
            if x.rdtype == dns.rdatatype.A:
                nodes[x.name.to_text().strip(".")] = x[0].address

        max_priority = max([r.priority for r in self.response.answer[0]])

        for record in self.response.answer[0]:
            if record.priority == max_priority:
                self.srv.append(
                    Entry(nodes[record.target.to_text().strip(".")], str(record.port))
                )
                self.weights.append(record.weight)


class ServiceARecord(BaseService):
    def _parse_response(self) -> None:
        """Parse the DNS response into something a little more useful.  PyDNS
        object model is too complicated for everyday use.
        We somtimes use A records in if we do not support (or cannot get) SRV Records
        """

        for record in self.response.answer[0]:
            self.srv.append(Entry(record.address, "0"))
            self.weights.append(100)


class ServiceExplicit(BaseService):
    def __init__(self, response):
        super().__init__(response)

    def _parse_response(self) -> None:
        """Explicit result just returns the address you passed into without
        resolution.  Useful mainly in test to avoid changing IP addresses"""

        self.srv.append(Entry(self.response, "0"))
        self.weights.append(100)


def discover_service(service_name: str, query: str = "SRV") -> BaseService:
    answer = None
    if os.getenv("FLASK_ENV") == "production":
        answer = BaseService.resolver().query(service_name, query)
        return ServiceSRVRecord(answer.response)
    elif query == "A":
        answer = BaseService.resolver().query(service_name, query)
        return ServiceARecord(answer.response)
    else:
        return ServiceExplicit(service_name)
