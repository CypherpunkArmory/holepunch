from app import db, momblish
from app.models import Subdomain
from app.utils.errors import SubdomainTaken, SubdomainInUse, SubdomainLimitReached

subdomain_reserved_limits = {"free": 0, "paid": 5, "beta": 5, "admin": 5}


class SubdomainCreationService:
    def __init__(self, current_user, subdomain_name=""):
        self.current_user = current_user
        self.subdomain_name = subdomain_name

    def over_subdomain_limits(self):
        num_reserved_subdomains = self.current_user.subdomains.filter_by(
            reserved=True
        ).count()
        if num_reserved_subdomains >= self.current_user.limits().reserved_subdomains:
            return True
        return False

    def get_unused_subdomain(self, tcp_url):
        while True:
            self.subdomain_name = momblish.word(10).lower()
            if tcp_url:
                self.subdomain_name = "TCP-" + self.subdomain_name
            try:
                subdomain = self.reserve(reserve=False)
                break
            except SubdomainTaken:
                continue
        return subdomain

    def reserve(self, reserve=True):
        if reserve:
            if self.over_subdomain_limits():
                raise SubdomainLimitReached(
                    "Maximum number of reserved subdomains reached"
                )
        subdomain_exist = (
            db.session.query(Subdomain.name)
            .filter_by(name=self.subdomain_name)
            .scalar()
        )

        if subdomain_exist:
            raise SubdomainTaken("Requested Subdomain is already reserved")

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

    def release(self) -> None:
        if self.subdomain.in_use:
            raise SubdomainInUse("Subdomain is in use")
        db.session.delete(self.subdomain)
        db.session.flush()
