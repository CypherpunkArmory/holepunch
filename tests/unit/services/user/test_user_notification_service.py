from unittest import mock
from app.services.user.user_notification import UserNotification
from tests.factories.user import UnconfirmedUserFactory, UserFactory


@mock.patch(
    "app.services.user.user_notification.send_beta_backlog_notification_email.queue",
    autospec=True,
)
@mock.patch(
    "app.services.user.user_notification.send_confirm_email.queue", autospec=True
)
class TestUserNotification(object):
    """ User Notification sends the right emails on signup """

    def test_waiting_users_get_the_backlog_email(self, send_confirm, send_beta):
        waiter = UserFactory(tier="waiting", confirmed=False)
        UserNotification(waiter).activation_emails()
        send_beta.assert_called_once()
        send_confirm.assert_not_called()

    def test_paid_users_get_the_welcome_email(self, send_confirm, send_beta):
        paid = UnconfirmedUserFactory()
        UserNotification(paid).activation_emails()
        send_beta.assert_not_called()
        send_confirm.assert_called_once()

    def test_confirmed_users_get_no_email(self, send_confirm, send_beta):
        paid_and_confirmed = UserFactory()
        UserNotification(paid_and_confirmed).activation_emails()
        send_beta.assert_not_called()
        send_confirm.assert_not_called()
