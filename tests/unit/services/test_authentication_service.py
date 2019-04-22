import time
import pytest
from app.services import authentication
from unittest import mock
from app.utils.errors import AccessDenied
from flask import url_for


class TestUtils(object):
    def test_verify_token(self):
        # Ensure encode and decode behave correctly.
        token = authentication.encode_token("dummy@email.com")
        email = authentication.decode_token(token)
        assert email == "dummy@email.com"

    def test_verify_invalid_token(self):
        # Ensure encode and decode behave correctly when token is invalid.
        token = "invalid"
        email = authentication.decode_token(token)
        assert email is False

    def test_verify_expired_token(self):
        # Ensure encode and decode behave correctly when token has expired.
        token = authentication.encode_token("dummy@email.com")
        time.sleep(1)
        email = authentication.decode_token(token, expiration=0)
        assert email is False

    def test_token_is_unique(self):
        # Ensure tokens are unique.
        token1 = authentication.encode_token("dummy@email.com")
        token2 = authentication.encode_token("dummy@email2.com")
        assert token1 != token2

    def test_generate_url(self):
        # Ensure generate_url behaves as expected.
        token = authentication.encode_token("dummy@email.com")
        url = url_for("account.confirm", token=token, _external=True)
        url_token = url.split("/")[-1]  # the last one
        assert token == url_token
        email = authentication.decode_token(url_token)
        assert email == "dummy@email.com"


@mock.patch(
    "app.services.authentication.get_jwt_claims",
    return_value={"scopes": ["test:foo", "test:bar"]},
)
class TestUtilsJWTScope:
    @authentication.jwt_scope_required(any_of=["test:baz", "test:bag"])
    def baz(self):
        return True

    @authentication.jwt_scope_required(all_of=["test:baz", "test:foo"])
    def foo_baz(self):
        return True

    @authentication.jwt_scope_required(
        any_of=["test:baz", "test:bar"], all_of=["test:foo"]
    )
    def baz_bar(self):
        return True

    def test_at_least_one_any_of(self, get_jwt_claims):
        """ Test AnyOf has at least one scope in list"""
        with pytest.raises(AccessDenied):
            # scopes do not include BAZ or BAG
            self.baz()

    def test_all_all_of(self, get_jwt_claims):
        """Test all_of includes all scopes in list"""
        get_jwt_claims.return_value = {"scopes": ["test:foo", "test:bar"]}
        with pytest.raises(AccessDenied):
            # scopes do not include both BAZ and FOO
            self.foo_baz()

    def test_any_and_all_combo(self, get_jwt_claims):
        """Combination includes at least one any_of and all all_of"""
        # scope includes bar and foo
        get_jwt_claims.return_value = {"scopes": ["test:foo", "test:bar"]}
        assert self.baz_bar() is True
