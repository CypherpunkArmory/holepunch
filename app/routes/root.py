from flask import Blueprint

root_blueprint = Blueprint("root", __name__)


@root_blueprint.route("/")
@root_blueprint.route("/index")
def index():
    return "Greetings User!"


@root_blueprint.route("/health_check")
def health_check():
    return "OK"
