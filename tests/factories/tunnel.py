from random import randint

from faker import Faker as RealFaker

from app.models import Tunnel
from factory import Factory, SubFactory
from pytest_factoryboy import register
from tests.factories.subdomain import SubdomainFactory

fake = RealFaker()


@register
class TunnelFactory(Factory):
    class Meta:
        model = Tunnel

    subdomain = SubFactory(SubdomainFactory)
    port = ["http"]
    ssh_port = randint(1000, 32678)
    job_id = f"ssh/dispatch-{randint(1000,3678)}"


@register
class HttpsTunnelFactory(TunnelFactory):
    port = ["https"]
