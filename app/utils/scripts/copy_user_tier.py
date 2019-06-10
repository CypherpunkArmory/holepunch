from app.commands import populate as plan_populate
from app.commands import create_product
from app import create_app, db
from flask_migrate import upgrade
import os
import sys
from sqlalchemy import orm
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):  # type: ignore
    __tablename__ = "user"

    id = sa.Column(sa.Integer, primary_key=True)
    tier = sa.Column(sa.String(64), nullable=False)
    plan_id = sa.Column(sa.Integer, sa.ForeignKey("plan.id", name="user_plan_fk"))
    plan = orm.relationship("Plan", lazy="joined")


class Plan(Base):  # type: ignore
    __tablename__ = "plan"

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String, index=True, nullable=False, unique=True)
    stripe_id = sa.Column(sa.String, index=True, unique=True)
    users = orm.relationship("User")


def pre(app):
    with app.app_context():
        upgrade(revision="1e1c9c5d8e58")

        plan_populate()

        app.logger.info("Moving Users to New Plans")
        for plan in db.session.query(Plan).all():
            db.session.query(User).filter_by(tier=plan.name).update(
                {User.plan_id: plan.id}, synchronize_session="fetch"
            )

        db.session.commit()
        db.session.expire_all()


def post(app):
    with app.app_context():
        upgrade(revision="3f63f2913228")
        create_product()


# deploy old code
# run upgrade which adds tasbles
# run data migration
# deploy new code
# run upgrade which drops tables

if __name__ == "__main__":
    app = create_app(os.environ.get("FLASK_ENV", "development"))
    if sys.argv[1] == "pre":
        pre(app)
    if sys.argv[1] == "post":
        post(app)
