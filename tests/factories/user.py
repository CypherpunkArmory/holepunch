from factory import Factory, post_generation, Faker, lazy_attribute
from pytest_factoryboy import register
import uuid

from app.models import User, Plan


@register
class UserFactory(Factory):
    class Meta:
        model = User

    class Params:
        tier = "paid"

    email = Faker("email")
    confirmed = True

    @post_generation
    def set_password(user, create, extracted, **kwargs):
        user.set_password("123123")

    @post_generation
    def set_uuid(user, create, extracted, **kwargs):
        user.uuid = str(uuid.uuid1())

    @lazy_attribute
    def plan(self):
        return Plan.query.filter_by(name=self.tier).first()


@register
class UnconfirmedUserFactory(UserFactory):
    confirmed = False
