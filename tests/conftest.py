import pytest
from dotenv import load_dotenv
from app import create_app, stripe
from app.commands import populate_redis
from app import db as _db
from sqlalchemy import event
from tests.support.client import TestClient
from tests.factories import user, plan as plan_factory
from functools import wraps
import time
from stripe.webhook import WebhookSignature
import json

collect_ignore = ["client.py"]


def mock_decorator():
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            return f(*args, **kwargs)

        return decorated_function

    return decorator


@pytest.fixture(scope="module")
def vcr_config():
    return {"filter_headers": [("authorization", "NOKEYFORYOU")]}


@pytest.fixture(scope="session")
def app(request):
    load_dotenv("/holepunch/.env.test", override=True)
    app = create_app("test")
    return app


@pytest.fixture(scope="session")
def db(app, request):
    with app.app_context():
        _db.drop_all()
        _db.create_all()


@pytest.fixture(scope="function")
def stripe_event(app):
    def _stripe_event(payload_dict):
        timestamp = int(time.time())
        payload = json.dumps(payload_dict)
        hmac = WebhookSignature._compute_signature(
            "%d.%s" % (timestamp, payload), app.config["STRIPE_ENDPOINT_SECRET"]
        )
        signature = f"t={timestamp},v1={hmac},v0={hmac}"

        return signature, payload

    return _stripe_event


@pytest.fixture(scope="function")
def attach_payment_method(app, session):
    def _attach_payment_method(user, stripe_pm_id):
        pm_id = stripe.PaymentMethod.attach(stripe_pm_id, customer=user.stripe_id).id
        user.stripe_payment_method = pm_id
        session.add(user)
        session.flush()

    return _attach_payment_method


@pytest.fixture(scope="session", autouse=True)
def populate_plans(app, db):
    with app.app_context():
        plans = ["paid", "free", "waiting", "beta", "admin"]
        sess = _db.create_scoped_session()
        for plan in plans:
            p = plan_factory.PlanFactory(**{plan: True})
            sess.add(p)

        sess.commit()
        sess.remove()
        sess.expire_all()


@pytest.fixture(scope="session", autouse=True)
def populate_redis_fixture():
    populate_redis()


@pytest.fixture(scope="function", autouse=True)
def session(app, db, request):
    with app.app_context():
        conn = _db.engine.connect()
        txn = conn.begin()

        options = dict(bind=conn, binds={})
        sess = _db.create_scoped_session(options=options)

        # establish  a SAVEPOINT just before beginning the test
        # (http://docs.sqlalchemy.org/en/latest/orm/session_transaction.html#using-savepoint)
        sess.begin_nested()

        @event.listens_for(sess(), "after_transaction_end")
        def restart_savepoint(sess2, trans):
            # Detecting whether this is indeed the nested transaction of the test
            if trans.nested and not trans._parent.nested:
                # The test should have normally called session.commit(),
                # but to be safe we explicitly expire the session
                sess2.expire_all()
                sess2.begin_nested()

        _db.session = sess
        yield sess

        # Cleanup
        sess.remove()
        # This instruction rollsback any commit that were executed in the tests.
        txn.rollback()
        conn.close()


@pytest.fixture
def client(app, current_user):
    app.test_client_class = TestClient
    return app.test_client(user=current_user)


@pytest.fixture
def admin_client(app, current_admin_user):
    app.test_client_class = TestClient
    return app.test_client(user=current_admin_user)


@pytest.fixture
def unauthenticated_client(app):
    return app.test_client()


@pytest.fixture
def free_client(app, current_free_user):
    app.test_client_class = TestClient
    return app.test_client(user=current_free_user)


@pytest.fixture
def refresh_client(app, current_user):
    app.test_client_class = TestClient
    return app.test_client(user=current_user, refresh=True)


@pytest.fixture
def current_user(session):
    u = user.UserFactory()
    session.add(u)
    session.flush()
    return u


@pytest.fixture
def current_free_user(session):
    u = user.UserFactory(tier="free")
    session.add(u)
    session.flush()
    return u


@pytest.fixture
def current_admin_user(session):
    u = user.UserFactory(tier="admin")
    session.add(u)
    session.flush()
    return u
