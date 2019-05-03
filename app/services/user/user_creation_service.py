from app import db
from app.models import User
from app.utils.errors import UserError
from sqlalchemy.exc import IntegrityError
import uuid


class UserCreationService:
    def __init__(self, **attrs):
        self.email = attrs.pop("email")
        self.password = attrs.pop("password")

    def create(self) -> User:
        try:
            new_user = User(
                email=self.email,
                confirmed=False,
                tier=self.get_user_tier(),
                uuid=str(uuid.uuid4()),
            )
            new_user.set_password(self.password)
            db.session.add(new_user)
            db.session.flush()
        except IntegrityError:
            raise UserError(detail="There is already a user with this email")

        return new_user

    def get_user_tier(self) -> str:
        if User.query.filter_by(confirmed=True).count() < 1000:
            return "beta"
        else:
            return "waiting"
