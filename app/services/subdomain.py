from app import db, momblish
from app.models import Subdomain
from app.utils.errors import AccessDenied, SubdomainTaken, SubdomainInUse


class SubdomainCreationService:
    def __init__(self, current_user, subdomain_name=""):
        self.current_user = current_user
        self.subdomain_name = subdomain_name

    def get_unused_subdomain(self):
        while True:
            self.subdomain_name = momblish.word(10).lower()
            try:
                subdomain = self.reserve(reserve=False)
                break
            except SubdomainTaken:
                continue
        return subdomain

    def reserve(self, reserve=True):
        subdomain_exist = (
            db.session.query(Subdomain.name)
            .filter_by(name=self.subdomain_name)
            .scalar()
        )

        if subdomain_exist:
            raise SubdomainTaken("")

        subdomain = Subdomain(
            user_id=self.current_user.id,
            name=self.subdomain_name,
            reserved=reserve,
            in_use=False,
        )

        db.session.add(subdomain)
        db.session.flush()

        return subdomain


class SubdomainDeletionService:
    def __init__(self, current_user, subdomain):
        self.current_user = current_user
        self.subdomain = subdomain

    def is_users(self) -> bool:
        return self.subdomain.user == self.current_user

    def release(self) -> None:
        if self.subdomain.in_use:
            raise SubdomainInUse("Subdomain is in use")
        db.session.delete(self.subdomain)
        db.session.flush()
