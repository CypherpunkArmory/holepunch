import stripe
import click
import json
from flask.cli import with_appcontext
from flask import current_app
from app.models import Plan
from app import db, redis_client
from stripe.error import InvalidRequestError


with open("support/plans.json") as plans:
    global LIMITS
    LIMITS = json.load(plans)


@click.group()
def plan():
    """ Manage Plan Tables """
    pass


@plan.command("stripe_product")
@with_appcontext
def create_product_command():
    create_product()


def create_product():
    """ Create Stripe Products for Holepunch """

    try:
        stripe.Product.retrieve("holepunch")
    except InvalidRequestError:
        stripe.Product.create(name="Holepunch.io", type="service", id="holepunch")

    for plan in Plan.query.all():
        if plan.cost == 0:
            continue

        if plan.stripe_id:
            try:
                stripe.Plan.retrieve(plan.stripe_id)
                current_app.logger.info(
                    f"Skipping `{plan.name}` as it already exists on Stripe"
                )
            except InvalidRequestError:
                pass  # expected for plans not created yet

        stripe_plan = stripe.Plan.create(
            product="holepunch",
            nickname=f"Holepunch Service: {plan.name}",
            interval="month",
            currency="usd",
            amount=plan.cost,
        )

        plan.stripe_id = stripe_plan["id"]
        db.session.add(plan)

    db.session.commit()


@plan.command("populate")
@with_appcontext
def populate_command():
    populate()


def populate():
    """ Create DB Entries for Holepunch Plans"""

    for plan_name, plan in LIMITS.items():
        p = Plan(**{"name": plan_name}, **plan)
        db.session.add(p)

    db.session.commit()


@click.group()
def redis():
    """ Manage Redis lists """
    pass


@redis.command("populate")
@with_appcontext
def populate_redis_command():
    populate_redis()


def populate_redis():
    """ Populate redis set"""
    ports = list(range(10000, 25000))
    redis_client.sadd("open_tcp_ports", *ports)
    redis_client.sadd("unhealthy_tunnels", 0)
