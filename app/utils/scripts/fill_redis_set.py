from app import create_app
from app.commands.redis import populate_redis
import sys


def pre(app):
    with app.app_context():
        populate_redis()


def post(app):
    pass


if __name__ == "__main__":
    app = create_app(os.environ.get("FLASK_ENV", "development"))
    if sys.argv[1] == "pre":
        pre(app)
    if sys.argv[1] == "post":
        post(app)
