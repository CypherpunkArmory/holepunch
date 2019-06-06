import stripe
import click
from flask.cli import with_appcontext
from app.models import Plan
from app import db

LIMITS = {
    "free": {
        "tunnel_count": 1,
        "bandwidth": 100,
        "forwards": 2,
        "reserved_subdomains": 0,
        "cost": 0,
    },
    "waiting": {
        "tunnel_count": 0,
        "bandwidth": 0,
        "forwards": 0,
        "reserved_subdomains": 0,
        "cost": 0,
    },
    "beta": {
        "tunnel_count": 2,
        "bandwidth": 1000,
        "forwards": 10,
        "reserved_subdomains": 1,
        "cost": 0,
    },
    "paid": {
        "tunnel_count": 5,
        "bandwidth": 100000,
        "forwards": 9999,
        "reserved_subdomains": 5,
        "cost": 999,
    },
}


@click.group()
def plan():
    """ Manage Plan Tables """
    pass


@plan.command("stripe_product")
@with_appcontext
def create_product():
    """ Create Stripe Products for Holepunch """
    for plan in Plan.query.all():
        if plan.cost == 0:
            continue

        stripe.Product.create(name="Holepunch.io", type="service", id=plan.name)
        stripe_plan = stripe.Plan.create(
            product=plan.name,
            nickname=f"Holepunch Service: {plan.name}",
            interval="month",
            currency="usd",
            amount=plan.cost,
        )

        plan.stripe_id = stripe_plan["product"]
        db.session.add(plan)

    db.session.commit()


@plan.command("populate")
@with_appcontext
def populate():
    """ Create DB Entries for Holepunch Plans"""

    for plan_name, plan in LIMITS.items():
        p = Plan(**{"name": plan_name}, **plan)
        db.session.add(p)

    db.session.commit()
