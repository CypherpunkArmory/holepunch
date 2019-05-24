from flask import Blueprint, jsonify, current_app
import os

root_blueprint = Blueprint("root", __name__)


@root_blueprint.route("/")
@root_blueprint.route("/index")
def index():
    return jsonify(
        {
            "greeting": "Greetings User!",
            "allocation": os.environ.get("NOMAD_ALLOC_ID"),
            "min_calver": current_app.config["MIN_CALVER"],
            "commit-sha": source_commit(),
        }
    )


@root_blueprint.route("/health_check")
def health_check():
    return "OK"


def source_commit():
    if current_app.env == "production":
        return open("./SOURCE_COMMIT").readline()
    else:
        return "none"
