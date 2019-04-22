from app.services.user import UserCreationService, UserNotificationService
from unittest import mock
from tests.factories.user import WaitingUserFactory, UnconfirmedUserFactory, UserFactory


class TestUserCreationService(object):
    """User creation service has correct logic"""

    @mock.patch("app.services.user.send_confirm_email.queue")
    @mock.patch("app.services.user.send_password_change_confirm_email.queue")
    def test_email_send_triggered_on_update(
        self, password_changed, registration_email, session
    ):
        UserCreationService(email="loser@hotmail.com", password="password").create()
        registration_email.assert_called_once()
        password_changed.assert_not_called()


@mock.patch(
    "app.services.user.send_beta_backlog_notification_email.queue", autospec=True
)
@mock.patch("app.services.user.send_confirm_email.queue", autospec=True)
class TestUserNotificationService(object):
    """ User Notification sends the right emails on signup """

    def test_waiting_users_get_the_backlog_email(self, send_confirm, send_beta):
        waiter = WaitingUserFactory()
        UserNotificationService(waiter).activation_emails()
        send_beta.assert_called_once()
        send_confirm.assert_not_called()

    def test_paid_users_get_the_welcome_email(self, send_confirm, send_beta):
        paid = UnconfirmedUserFactory()
        UserNotificationService(paid).activation_emails()
        send_beta.assert_not_called()
        send_confirm.assert_called_once()

    def test_confirmed_users_get_no_email(self, send_confirm, send_beta):
        paid_and_confirmed = UserFactory()
        UserNotificationService(paid_and_confirmed).activation_emails()
        send_beta.assert_not_called()
        send_confirm.assert_not_called()
