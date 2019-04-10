import time
from app.services import authentication


class TestUtils(object):

    email_confirm_salt = "email-confirm-salt"

    def test_verify_token(self):
        # Ensure encode and decode behave correctly.
        token = authentication.encode_token("dummy@email.com", self.email_confirm_salt)
        email = authentication.decode_token(token, self.email_confirm_salt)
        assert email == "dummy@email.com"

    def test_verify_invalid_token(self):
        # Ensure encode and decode behave correctly when token is invalid.
        token = "invalid"
        email = authentication.decode_token(token, self.email_confirm_salt)
        assert email == False

    def test_verify_expired_token(self):
        # Ensure encode and decode behave correctly when token has expired.
        token = authentication.encode_token("dummy@email.com", self.email_confirm_salt)
        time.sleep(1)
        email = authentication.decode_token(token, self.email_confirm_salt, 0)
        assert email == False

    def test_token_is_unique(self):
        # Ensure tokens are unique.
        token1 = authentication.encode_token("dummy@email.com", self.email_confirm_salt)
        token2 = authentication.encode_token(
            "dummy@email2.com", self.email_confirm_salt
        )
        assert token1 != token2

    def test_generate_url(self):
        # Ensure generate_url behaves as expected.
        token = authentication.encode_token("dummy@email.com", self.email_confirm_salt)
        url = authentication.generate_registration_url(token)
        url_token = url.split("/")[4]
        assert token == url_token
        email = authentication.decode_token(url_token, self.email_confirm_salt)
        assert email == "dummy@email.com"
