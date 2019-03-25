import pytest
from app.jobs.email import send_confirm_email, send_password_change_confirm_email
from app.services.authentication import encode_token, generate_registration_url
import requests


class TestEmailJob(object):
    """Email job sends correct email"""

    def test_email_job(self, current_user):
        """ The email is sent correctly"""
        r = requests.get("http://mail:8025/api/v1/events", stream=True)
        r.encoding = "ascii"

        token = encode_token(current_user.email)
        confirm_url = generate_registration_url(token)
        send_confirm_email(current_user.email, confirm_url)

        for line in r.iter_lines(decode_unicode=True):
            if line and current_user.email in line:
                r.close()
                break

    def test_email_job_when_mail_server_is_down(self, current_user):
        """ Raises an exception when the email cannot be sent"""
        url = "http://mail:8025/api/v2/jim"

        try:
            requests.post(url, json={"RejectAuthChance": 1.0})

            with pytest.raises(Exception):
                send_confirm_email(current_user.email, "DEADBEEF")

        finally:
            requests.delete(url)

    def test_email_change_password_confirmation(self, current_user):
        """ The email is sent correctly"""
        r = requests.get("http://mail:8025/api/v1/events", stream=True)

        send_password_change_confirm_email(current_user.email)

        if r.encoding is None:
            r.encoding = "ascii"

        for line in r.iter_lines(decode_unicode=True):
            if line and current_user.email in line:
                r.close()
                break
