from factory import Factory, post_generation, Faker
from faker import Faker as RealFaker
from pytest_factoryboy import register

from app.models import User

fake = RealFaker()


@register
class UserFactory(Factory):
    class Meta:
        model = User

    email = Faker("email")
    confirmed = True
    tier = "paid"

    @post_generation
    def set_password(user, create, extracted, **kwargs):
        user.set_password("123123")


@register
class FreeUserFactory(UserFactory):
    tier = "free"


@register
class WaitingUserFactory(UserFactory):
    confirmed = False
    tier = "waiting"


@register
class UnconfirmedUserFactory(UserFactory):
    confirmed = False
