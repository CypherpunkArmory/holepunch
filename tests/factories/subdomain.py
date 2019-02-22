from factory import Factory, SubFactory, fuzzy
from faker import Faker as RealFaker
from pytest_factoryboy import register

from app.models import Subdomain
from tests.factories.user import UserFactory

fake = RealFaker()


@register
class SubdomainFactory(Factory):
    class Meta:
        model = Subdomain

    user = SubFactory(UserFactory)
    in_use = False
    reserved = False
    name = fuzzy.FuzzyText()
    id = fuzzy.FuzzyInteger(1, 213)


@register
class ReservedSubdomainFactory(SubdomainFactory):
    reserved = True


@register
class InuseSubdomainFactory(SubdomainFactory):
    in_use = True


@register
class InuseReservedSubdomainFactory(SubdomainFactory):
    in_use = True
    reserved = True


@register
class InuseUnreservedSubdomainFactory(SubdomainFactory):
    in_use = True
    reserved = False
