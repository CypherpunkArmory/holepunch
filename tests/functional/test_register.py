from tests.factories.user import UserFactory


class TestRegister(object):
    """A User can register"""

    def test_root_accessible(self, client):
        """Root url is accessible with no login"""
        res = client.get("/")
        assert res.get_data() == b"Greetings User!"

    def test_register_with_email_and_password(self, client):
        """Post to /user url returns a 204 on success"""

        res = client.post(
            "/user", json={"email": "testing@example.com", "password": "123123"}
        )

        assert res.status_code == 204

    def test_register_with_taken_email(self, client, session):
        """Post to register url with taken email fails"""

        user = UserFactory(email="test@example.com")
        session.add(user)
        session.flush()

        res = client.post(
            "/user", json={"email": "test@example.com", "password": "123123"}
        )

        assert res.status_code == 422
