import os
import traceback

from dotenv import load_dotenv
from flask import Flask, request, got_request_exception
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import DatabaseError
from momblish import Momblish
from momblish.corpus import Corpus
from flask_cors import CORS
from flask_rq2 import RQ
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.contrib.fixers import ProxyFix
import rollbar
import rollbar.contrib.flask
from packaging import version

from app.utils.json import JSONSchemaManager, json_api

# this is kinda tacky - we should look to see if there's a environment autoloader
# this has to be checked against the actual environment in order to load the .env
# file in production and boot the app correctly
if os.getenv("FLASK_ENV") == "production":
    load_dotenv("/holepunch/.env.production")
    from ddtrace import patch_all

    patch_all()


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

    # This is required for route limits to be effective while behind Fabio.
    app.wsgi_app = ProxyFix(app.wsgi_app, num_proxies=1)  # type: ignore
    if env != "test":
        limiter = Limiter(app, key_func=get_remote_address)
        limiter.limit("3/second")(auth_blueprint)

    app.register_blueprint(auth_blueprint)
    app.register_blueprint(tunnel_blueprint)
    app.register_blueprint(subdomain_blueprint)
    app.register_blueprint(account_blueprint)
    app.register_blueprint(root_blueprint)

    from app.serializers import ErrorSchema
    from app.utils.errors import (
        OldAPIVersion,
        MalformedAPIHeader,
        TooManyRequestsError,
        NotFoundError,
        InternalServerError,
    )
    import re

    @app.shell_context_processor
    def ctx():
        return {"app": app, "db": db}

    @app.before_first_request
    def init_rollbar():
        if env == "production":
            rollbar.init(
                app.config["ROLLBAR_TOKEN"],
                env,
                # server root directory, makes tracebacks prettier
                root=os.path.dirname(os.path.realpath(__file__)),
                # flask already sets up logging
                allow_logging_basic_config=False,
            )

            # send exceptions from `app` to rollbar, using flask's signal system.
            got_request_exception.connect(rollbar.contrib.flask.report_exception, app)

    @app.errorhandler(429)
    def too_many_requests(_):
        return json_api(TooManyRequestsError, ErrorSchema), 429

    @app.errorhandler(500)
    def debug_error_handler(e):
        if env == "production":
            return json_api(InternalServerError, ErrorSchema), 500
        else:
            return (
                json_api(
                    InternalServerError(
                        detail=str(e), backtrace=traceback.format_exc().split("\n")
                    ),
                    ErrorSchema,
                ),
                500,
            )

    @app.errorhandler(404)
    def page_not_found(e):
        return json_api(NotFoundError(detail=e.description), ErrorSchema), 404

    @app.before_request
    def parse_query_params():
        if request.query_string:
            request.query_params = qs_parse(request.query_string)
        else:
            request.query_params = dict()

    def check_version(date):
        return version.parse(date) >= version.parse(app.config["MIN_CALVER"])

    @app.before_request
    def check_api_version():
        if "Api-Version" in request.headers:
            if not re.match(r"^\d+\.\d+\.\d+\.\d+$", request.headers["Api-Version"]):
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
