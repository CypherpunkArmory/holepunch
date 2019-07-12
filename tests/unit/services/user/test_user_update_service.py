from unittest import mock
from tests.factories.user import UserFactory
from app.services.user.user_update import UserUpdate
from app.models import Plan
from app import db


class TestUserUpdate(object):
    """ User Update Service fires all the right hooks. """

    def test_user_can_change_relationship(self, session):
        free_user = UserFactory(tier="free")
        plan = Plan.paid()
        session.add(free_user)
        session.flush()

        user = UserUpdate(
            user=free_user,
            rels={"plan": {"data": {"type": "plan", "id": str(plan.id)}}},
        ).update()

        assert user.plan == plan

    @mock.patch("app.jobs.payment.user_subscribed.queue")
    def test_user_subscribed_is_run_when_user_tier_is_changed_to_paid(
        self, user_subscribed, session
    ):
        free_user = UserFactory(tier="free")

        UserUpdate(
            user=free_user,
            rels={"plan": {"data": {"type": "plan", "id": str(Plan.paid().id)}}},
        ).update()

        db.session.commit()

        user_subscribed.assert_called_with(free_user.id, Plan.paid().id)

    @mock.patch("app.jobs.payment.user_unsubscribed.queue")
    def test_user_unsubscribed_is_run_when_user_tier_is_changed_to_free(
        self, user_unsubscribed, session
    ):
        user = UserFactory()
        db.session.add(user)
        db.session.flush()

        UserUpdate(
            user=user,
            rels={"plan": {"data": {"type": "plan", "id": str(Plan.free().id)}}},
        ).update()

        db.session.commit()

        user_unsubscribed.assert_called_with(user.id, Plan.paid().id)

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

        UserUpdate(
            user=free_user,
            rels={"plan": {"data": {"type": "plan", "id": str(Plan.paid().id)}}},
        ).update()

        session.commit()
        session.expire_all()

        user_subscribed.assert_called_with(free_user.id, Plan.paid().id)
        user_subscribed.reset_mock()

        sess = db.create_scoped_session()

        free_user2 = UserFactory(tier="free", email="some_other@email.com")

        UserUpdate(
            user=free_user2,
            rels={"plan": {"data": {"type": "plan", "id": str(Plan.free().id)}}},
        ).update()

        session.commit()

        user_subscribed.assert_not_called()

        sess.remove()
