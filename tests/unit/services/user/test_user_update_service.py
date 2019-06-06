from unittest import mock
from tests.factories.user import UserFactory
from app.models import Plan
from app import db


class TestUserUpdate(object):
    """ User Update Service fires all the right hooks. """

    @mock.patch("app.jobs.payment.user_subscribed.queue")
    def test_user_subscribed_is_run_when_user_tier_is_changed_to_paid(
        self, user_subscribed, session
    ):
        free_user = UserFactory(tier="free")
        free_user.plan = Plan.paid()
        session.add(free_user)
        session.commit()
        user_subscribed.assert_called_with(free_user.id, Plan.paid().id)

    @mock.patch("app.jobs.payment.user_unsubscribed.queue")
    def test_user_unsubscribed_is_run_when_user_tier_is_changed_to_free(
        self, user_unsubscribed, session
    ):
        user = UserFactory()
        user.plan = Plan.free()
        session.add(user)
        session.commit()
        user_unsubscribed.assert_called_with(user.id)

    @mock.patch("app.jobs.payment.user_subscribed.queue")
    def test_after_commit_hooks_are_specific_to_a_session(
        self, user_subscribed, session, app
    ):

        # What does this test prove? Well - we start by showing
        # the thing works and by setting up a an "after_commit" hook
        # on the session.  (There SHOULD BE one session per request.)
        # The next request should NOT fire the "after_commit" hook
        # because it has a new session.  IE - we are not leaking
        # Model instances across requests, and not firing subscribe
        # events for instances we didn't change

        free_user = UserFactory(tier="free")
        free_user.plan = Plan.paid()

        session.add(free_user)
        session.commit()
        session.expire_all()

        user_subscribed.assert_called_with(free_user.id, Plan.paid().id)
        user_subscribed.reset_mock()

        sess = db.create_scoped_session()

        free_user2 = UserFactory(tier="free", email="some_other@email.com")
        session.expunge(free_user2.plan)
        sess.add(free_user2)
        sess.commit()
        user_subscribed.assert_not_called()

        sess.remove()
