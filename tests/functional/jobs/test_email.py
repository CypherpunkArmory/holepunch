import pytest
from app.jobs.email import (
    send_confirm_email,
    send_password_change_confirm_email,
    send_password_reset_confirm_email,
    send_beta_backlog_notification_email,
    send_email_change_confirm_email,
)
import requests


class TestEmailJob(object):
    """Email job sends correct email"""

    def test_email_job(self, current_user):
        """ The email is sent correctly"""
        r = requests.get("http://mail:8025/api/v1/events", stream=True)
        r.encoding = "ascii"

        send_confirm_email(current_user.email, "sample-url.com/token")

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

    def test_email_reset_password_confirmation(
        self, unauthenticated_client, current_user
    ):
        """ The reset password email is sent correctly"""
        r = requests.get("http://mail:8025/api/v1/events", stream=True, timeout=15)
        r.encoding = "ascii"

        send_password_reset_confirm_email(current_user.email, "sample-url.com/token")

        for line in r.iter_lines(decode_unicode=True):
            if line and current_user.email in line:
                r.close()
                break

    def test_beta_backlog_notification_email(
        self, unauthenticated_client, current_user
    ):
        """ The Beta backlog notification email is sent correctly"""
        r = requests.get("http://mail:8025/api/v1/events", stream=True, timeout=15)
        r.encoding = "ascii"

        send_beta_backlog_notification_email(current_user.email)

        for line in r.iter_lines(decode_unicode=True):
            if line and current_user.email in line:
                r.close()
                break

    def test_email_change_confirm_email(self, unauthenticated_client, current_user):
        """ The Beta backlog notification email is sent correctly"""
        r = requests.get("http://mail:8025/api/v1/events", stream=True, timeout=15)
        r.encoding = "ascii"

        send_email_change_confirm_email(current_user.email)

        for line in r.iter_lines(decode_unicode=True):
            if line and current_user.email in line:
                r.close()
                break
