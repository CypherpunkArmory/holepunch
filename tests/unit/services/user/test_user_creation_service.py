from app.services.user.user_creation import UserCreation
from unittest import mock


class TestUserCreation(object):
    """User creation service has correct logic"""

    @mock.patch("app.services.user.user_notification.send_confirm_email.queue")
    @mock.patch(
        "app.services.user.user_notification.send_password_change_confirm_email.queue"
    )
    def test_email_send_triggered_on_update(
        self, password_changed, registration_email, session
    ):
        UserCreation(email="loser@hotmail.com", password="password").create()
        registration_email.assert_called_once()
        password_changed.assert_not_called()
