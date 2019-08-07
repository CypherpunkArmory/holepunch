import jwt
import uuid
import datetime
import time
from werkzeug.datastructures import Headers
from flask.testing import FlaskClient
from app.routes.authentication import ensure_user_claims
from flask import current_app


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
                "exp": int(time.time()) + 1000,
                "identity": current_user.uuid,
                "type": ("refresh" if refresh is True else "access"),
                "fresh": True,
                "user_claims": ensure_user_claims(current_user.email),
            }

            access_token = jwt.encode(
                token_data, current_app.config["JWT_SECRET_KEY"], "HS256"
            )
            self._token = access_token.decode("utf-8")

        super(TestClient, self).__init__(*args, **kwargs)

    def open(self, *args, **kwargs):
        if self._token:
            api_headers = Headers(
                {
                    "Authorization": f"Bearer {self._token}",
                    "Content-Type": "application/vnd.api+json",
                    "Api-Version": current_app.config["MIN_CALVER"],
                }
            )

            headers = kwargs.pop("headers", Headers())
            headers.extend(api_headers)
            kwargs["headers"] = headers

        return super().open(*args, **kwargs)
