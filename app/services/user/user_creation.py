from app import db
from app.models import User, Plan
from app.utils.errors import UserError
import uuid


class UserCreation:
    def __init__(self, **attrs):
        self.email = attrs.pop("email")
        self.password = attrs.pop("password")

    def create(self) -> User:
        if User.query.filter_by(email=self.email).first():
            raise UserError(detail="Email already in use")

        new_user = User(
            email=self.email,
            confirmed=False,
            plan=self.get_user_plan(),
            uuid=str(uuid.uuid4()),
        )
        new_user.set_password(self.password)
        db.session.add(new_user)
        db.session.flush()

        return new_user

    def get_user_plan(self) -> str:
        if User.query.filter_by(confirmed=True).count() < 1000:
            return Plan.beta()
        else:
            return Plan.waiting()
