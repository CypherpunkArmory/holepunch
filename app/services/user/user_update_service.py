from app import db
from app.services import authentication
from app.models import User
from app.utils.errors import AccessDenied, UserError


class UserUpdateService:
    def __init__(self, user: User, **attrs):
        self.user = user
        self.scopes = attrs.pop("scopes")
        authentication.validate_scope_permissions("update:user", self.scopes, attrs)
        self.new_password = attrs.pop("new_password", None)
        self.old_password = attrs.pop("old_password", None)
        self.email = attrs.pop("email", None)
        self.attrs = attrs

    def update(self) -> User:
        for attr, val in self.attrs.items():
            setattr(self.user, attr, val)

        # password is special cased because we encrypt it before
        # we actually store it.
        if self.new_password:
            if (
                "update:user:new_password" not in self.scopes
                and not self.user.check_password(self.old_password)
            ):
                raise AccessDenied("Wrong password")
            self.user.set_password(self.new_password)

        # email is also special cased in the sense of we do not attempt
        # to perform the write if we know there is a conflicting email
        if self.email:
            if User.query.filter_by(email=self.email).first() is not None:
                raise UserError(detail="Email already in use")
            self.user.email = self.email

        db.session.add(self.user)
        db.session.flush()

        return self.user
