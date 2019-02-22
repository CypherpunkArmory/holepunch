from tests.factories.user import UserFactory
from app.jobs.email import send_confirm_email
from app.services.authentication import (
    encode_token,
    decode_token,
    send_confirm_email,
    generate_registration_url,
)
import requests
import time


class TestEmailJob(object):
    """Email job sends correct email"""

    def test_email_job(self, current_user):
        """ The email is sent correctly"""
        url = "http://mail:8025/api/v2/messages"
        response = requests.get(url)
        data = response.json()
        old_total = data["total"]
        token = encode_token(current_user.email)
        confirm_url = generate_registration_url(token)
        send_confirm_email.queue(current_user.email, confirm_url)
        try:
            send_confirm_email("localhost/", current_user.id)
        except Exception as e:
            assert e
        time.sleep(1)
        response = requests.get(url)
        data = response.json()
        new_total = data["total"]
        assert new_total > old_total
