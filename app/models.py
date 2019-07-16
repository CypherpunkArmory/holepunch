from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy import types
from werkzeug import check_password_hash, generate_password_hash
from app import db
from sqlalchemy.dialects.postgresql import UUID
from typing import NamedTuple


class UserLimit(NamedTuple):
    tunnel_count: int
    bandwidth: int
    forwards: int
    reserved_subdomains: int


class Subdomain(db.Model):  # type: ignore
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, nullable=False, unique=True)
    reserved = db.Column(db.Boolean)
    in_use = db.Column(db.Boolean, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    user = db.relationship("User", back_populates="subdomains", lazy="joined")

    def __repr__(self):
        return "<Subdomain {}>".format(self.name)


class Plan(db.Model):  # type: ignore
    id = db.Column(db.Integer, primary_key=True)
    tunnel_count = db.Column(db.Integer)
    bandwidth = db.Column(db.Integer)
    forwards = db.Column(db.Integer)
    reserved_subdomains = db.Column(db.Integer)
    cost = db.Column(db.Integer)
    name = db.Column(db.String, index=True, nullable=False, unique=True)
    stripe_id = db.Column(db.String, index=True, unique=True)
    users = db.relationship("User")

    @staticmethod
    def paid():
        return Plan.query.filter_by(name="paid").first()

    @staticmethod
    def free():
        return Plan.query.filter_by(name="free").first()

    @staticmethod
    def beta():
        return Plan.query.filter_by(name="beta").first()

    @staticmethod
    def waiting():
        return Plan.query.filter_by(name="waiting").first()

    def __repr__(self):
        return "<Plan {}>".format(self.name)

    def limits(self):
        return UserLimit(
            tunnel_count=self.tunnel_count,
            bandwidth=self.bandwidth,
            forwards=self.forwards,
            reserved_subdomains=self.reserved_subdomains,
        )


class User(db.Model):  # type: ignore
    id = db.Column(db.Integer, primary_key=True)
    confirmed = db.Column(db.Boolean)
    email = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    uuid = db.Column(UUID(as_uuid=True), nullable=False, unique=True)
    plan_id = db.Column(db.Integer, db.ForeignKey("plan.id", name="user_plan_fk"))
    subdomains = db.relationship(
        "Subdomain", back_populates="user", lazy="dynamic", cascade="all, delete"
    )
    tunnels = db.relationship("Tunnel", secondary="subdomain", lazy="dynamic")
    plan = db.relationship("Plan", lazy="joined")

    def __repr__(self):
        return "<User {}>".format(self.email)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def limits(self):
        return self.plan.limits()

    def tier(self):
        return self.plan.name


class Tunnel(db.Model):  # type: ignore
    id = db.Column(db.Integer, primary_key=True)
    port = db.Column(types.ARRAY(types.String()))
    allocated_tcp_ports = db.Column(types.ARRAY(types.Integer()))
    subdomain_id = db.Column(db.Integer, db.ForeignKey("subdomain.id"))
    ssh_port = db.Column(db.Integer)
    job_id = db.Column(db.String(64))
    ip_address = db.Column(db.String(32))
    subdomain = db.relationship("Subdomain", backref="tunnel", lazy="joined")

    user = association_proxy("subdomain", "user")

    def __repr__(self):
        return "<Tunnel {} {}>".format(self.subdomain, self.job_id)
