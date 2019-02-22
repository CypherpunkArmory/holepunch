from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy import types
from werkzeug import check_password_hash, generate_password_hash

from app import db


class Subdomain(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, nullable=False, unique=True)
    reserved = db.Column(db.Boolean)
    in_use = db.Column(db.Boolean, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    user = db.relationship("User", back_populates="subdomains", lazy="joined")

    def __repr__(self):
        return "<Subdomain {}>".format(self.name)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    confirmed = db.Column(db.Boolean)
    email = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    subdomains = db.relationship("Subdomain", back_populates="user", lazy="dynamic")
    tunnels = db.relationship("Tunnel", secondary="subdomain", lazy="dynamic")

    def __repr__(self):
        return "<User {}>".format(self.email)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Tunnel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    port = db.Column(types.ARRAY(types.String()))
    subdomain_id = db.Column(db.Integer, db.ForeignKey("subdomain.id"))
    ssh_port = db.Column(db.Integer)
    job_id = db.Column(db.String(64))
    ip_address = db.Column(db.String(32))
    subdomain = db.relationship("Subdomain", backref="tunnel", lazy="joined")

    user = association_proxy("subdomain", "user")

    def __repr__(self):
        return "<Tunnel {} {}>".format(self.subdomain, self.job_id)
