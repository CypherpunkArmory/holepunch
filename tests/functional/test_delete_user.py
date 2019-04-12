from app.models import User


class TestDeleteUser(object):
    """A User can delete their account"""

    def test_delete_user(self, client, current_user):
        """Delete to /user/<user_id> url succeeds and user does not exist"""

        delete_user_url = "/user/" + str(current_user.id)
        res = client.delete(delete_user_url)

        user = User.query.filter_by(email=current_user.email).first()
        assert res.status_code == 204
        assert user == None

    def test_delete_wrong_user(self, client, current_user):
        """Delete to /user/<user_id> url succeeds and user does still exists"""

        delete_user_url = "/user/" + str(current_user.id + 1)
        res = client.delete(delete_user_url)

        user = User.query.filter_by(email=current_user.email).first()
        assert res.status_code == 404
        assert user != None
