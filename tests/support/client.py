import jwt
import uuid
import datetime
import os
from werkzeug.datastructures import Headers
from flask.testing import FlaskClient
from app.routes.authentication import ensure_user_claims
import requests
import json


class TestClient(FlaskClient):
    def __init__(self, *args, **kwargs):
        self._token = None
        current_user = kwargs.pop("user", None)
        refresh = kwargs.pop("refresh", False)

        if current_user:
            uid = str(uuid.uuid4())
            now = datetime.datetime.utcnow()
            token_data = {
                "iat": now,
                "nbf": now,
                "jti": uid,
                "identity": current_user.email,
                "type": ("refresh" if refresh is True else "access"),
                "fresh": True,
                "user_claims": ensure_user_claims(current_user.email),
            }

            access_token = jwt.encode(token_data, os.getenv("JWT_SECRET_KEY"), "HS256")
            self._token = access_token.decode("utf-8")

        super(TestClient, self).__init__(*args, **kwargs)

    def open(self, *args, **kwargs):
        if self._token:
            api_headers = Headers(
                {
                    "Authorization": f"Bearer {self._token}",
                    "Content-Type": "application/vnd.api+json",
                    "Api-Version": os.getenv("MIN_CALVER"),
                }
            )

            headers = kwargs.pop("headers", Headers())
            headers.extend(api_headers)
            kwargs["headers"] = headers

        return super().open(*args, **kwargs)
