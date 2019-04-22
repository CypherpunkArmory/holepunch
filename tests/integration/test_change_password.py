from app.models import User
from unittest import mock
import re
import requests


class TestChangePassword(object):
    """An authenticated User can change password"""

    def test_change_password_as_unauthenticated_user(
        self, unauthenticated_client, client, current_user
    ):
        """ The whole process of changing your password without knowing it"""

        events_r = requests.get(
            "http://mail:8025/api/v1/events", stream=True, timeout=30
        )
        events_r.encoding = "ascii"

        res = unauthenticated_client.post(
            "/account/token",
            json={
                "data": {
                    "type": "password_reset",
                    "attributes": {"email": current_user.email},
                }
            },
        )

        assert res.status_code == 200

        reset_url = ""
        pattern = None

        for line in events_r.iter_lines(decode_unicode=True):
            if line and current_user.email in line:
                pattern = re.compile(
                    r"(http:\/\/localhost:5000\/account\/confirm\/(.*?))\\r"
                )
            elif pattern:
                if pattern.search(line):
                    reset_url = pattern.search(line).group(1)
                    events_r.close()
                    break

        res = unauthenticated_client.get(reset_url)
        assert res.status_code is 200

        client._token = res.json["access_token"]

        res = client.patch(
            "/account",
            json={"data": {"type": "user", "attributes": {"new_password": "abc123"}}},
        )

        user = User.query.filter_by(email=current_user.email).first()
        assert res.status_code == 200
        assert user.check_password("abc123") is True
