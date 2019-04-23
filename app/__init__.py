import os
import traceback

import consul
from dotenv import load_dotenv
from flask import Flask, jsonify, request, got_request_exception
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import DatabaseError
from momblish import Momblish
from momblish.corpus import Corpus
from momblish.corpus_analyzer import CorpusAnalyzer
from flask_cors import CORS
from flask_rq2 import RQ
import rollbar
import rollbar.contrib.flask
from packaging import version

from app.utils.json import JSONSchemaManager, json_api, dig
from app.utils.dns import discover_service

# this is kinda tacky - we should look to see if there's a environment autoloader
if os.getenv("FLASK_ENV") == "production":
    load_dotenv("/holepunch/.env.production")
    from ddtrace import patch

    patch(flask=True, psycopg=True)


def load_corpus():
    mombler = Momblish(corpus=Corpus.load("support/corpus.json"))
    return mombler


db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
momblish = load_corpus()
json_schema_manager = JSONSchemaManager("../support/schemas")
Q = RQ()


def create_app(env: str = "development"):
    import app.settings as settings

    app = Flask(__name__)
    app.config.from_object(settings.app_config[env])

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    json_schema_manager.init_app(app)
    Q.init_app(app)
    CORS(app)

    from app.routes.tunnels import tunnel_blueprint
    from app.routes.subdomains import subdomain_blueprint
    from app.routes.authentication import auth_blueprint
    from app.routes.account import account_blueprint
    from app.routes.root import root_blueprint

    from querystring_parser.parser import parse as qs_parse

    app.register_blueprint(auth_blueprint)
    app.register_blueprint(tunnel_blueprint)
    app.register_blueprint(subdomain_blueprint)
    app.register_blueprint(account_blueprint)
    app.register_blueprint(root_blueprint)

    from app.serializers import ErrorSchema
    from app.utils.errors import OldAPIVersion, MalformedAPIHeader
    import re

    @app.shell_context_processor
    def ctx():
        return {"app": app, "db": db}

    @app.before_first_request
    def init_rollbar():
        if os.getenv("FLASK_ENV") == "production":
            rollbar.init(
                os.getenv("ROLLBAR_TOKEN"),
                os.getenv("FLASK_ENV"),
                # server root directory, makes tracebacks prettier
                root=os.path.dirname(os.path.realpath(__file__)),
                # flask already sets up logging
                allow_logging_basic_config=False,
            )

            # send exceptions from `app` to rollbar, using flask's signal system.
            got_request_exception.connect(rollbar.contrib.flask.report_exception, app)

    @app.errorhandler(500)
    def debug_error_handler(e):
        return (
            jsonify(
                error=500, text=str(e), exception=traceback.format_exc().split("\n")
            ),
            500,
        )

    @app.before_request
    def parse_query_params():
        if request.query_string:
            request.query_params = qs_parse(request.query_string)
        else:
            request.query_params = dict()

    def check_version(date):
        return version.parse(date) >= version.parse(os.getenv("MIN_CALVER"))

    @app.before_request
    def check_api_version():
        if "Api-Version" in request.headers:
            if not re.match("^\d+\.\d+\.\d+\.\d+$", request.headers["Api-Version"]):
                return json_api(MalformedAPIHeader, ErrorSchema), 403
            if check_version(request.headers["Api-Version"]):
                return
            else:
                return json_api(OldAPIVersion, ErrorSchema), 400

    @app.after_request
    def session_commit(response):
        if response.status_code >= 400:
            return response
        try:
            db.session.commit()
        except DatabaseError:
            db.session.rollback()
            raise

        return response

    return app
