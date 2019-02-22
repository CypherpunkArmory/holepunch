import pytest

from app.jobs.email import send_confirm_email
from app.services.authentication import (
    encode_token,
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
        send_confirm_email(current_user.email, confirm_url)

        time.sleep(1)
        response = requests.get(url)
        data = response.json()
        new_total = data["total"]
        assert new_total > old_total

    def test_email_job_when_mail_server_is_down(self, current_user):
        """ Raises an exception when the email cannot be sent"""
        url = "http://mail:8025/api/v2/jim"

        try:
            requests.post(url, json={"RejectAuthChance": 1.0})
            time.sleep(1)

            with pytest.raises(Exception):
                send_confirm_email(current_user.email, 'DEADBEEF')

        finally:
            requests.delete(url)
