from app.models import User
from app import db
from flask_jwt_extended import create_access_token


class UserToken:
    def __init__(self, uuid):
        self.uuid = uuid

    def confirm(self):
        user = User.query.filter_by(uuid=self.uuid).first()
        if user is None:
            return False
        user.confirmed = True
        db.session.add(user)
        db.session.flush()

        return True

    def issue_task_token(self, task):
        return create_access_token(identity=self.uuid, user_claims={"scopes": [task]})
