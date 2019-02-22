import jwt
import uuid
import datetime
import os
from werkzeug.datastructures import Headers
from flask.testing import FlaskClient


class TestClient(FlaskClient):
    def __init__(self, *args, **kwargs):
        current_user = kwargs.pop("user")

        uid = str(uuid.uuid4())
        now = datetime.datetime.utcnow()
        token_data = {
            "iat": now,
            "nbf": now,
            "jti": uid,
            "identity": current_user.email,
            "type": "access",
            "fresh": True,
        }

        access_token = jwt.encode(token_data, os.getenv("JWT_SECRET_KEY"), "HS256")
        self._token = access_token.decode("utf-8")

        super(TestClient, self).__init__(*args, **kwargs)

    def open(self, *args, **kwargs):
        api_headers = Headers(
            {
                "Authorization": f"Bearer {self._token}",
                "Content-Type": "application/vnd.api+json",
            }
        )

        headers = kwargs.pop("headers", Headers())
        headers.extend(api_headers)
        kwargs["headers"] = headers

        return super().open(*args, **kwargs)


class TestClientSession(FlaskClient):
    def __init__(self, *args, **kwargs):
        current_user = kwargs.pop("user")

        uid = str(uuid.uuid4())
        now = datetime.datetime.utcnow()
        token_data = {
            "iat": now,
            "nbf": now,
            "jti": uid,
            "identity": current_user.email,
            "type": "refresh",
            "fresh": True,
        }

        access_token = jwt.encode(token_data, os.getenv("JWT_SECRET_KEY"), "HS256")
        self._token = access_token.decode("utf-8")

        super(TestClientSession, self).__init__(*args, **kwargs)

    def open(self, *args, **kwargs):
        api_headers = Headers(
            {
                "Authorization": f"Bearer {self._token}",
                "Content-Type": "application/vnd.api+json",
            }
        )

        headers = kwargs.pop("headers", Headers())
        headers.extend(api_headers)
        kwargs["headers"] = headers

        return super().open(*args, **kwargs)
