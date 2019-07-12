import json
import os
import importlib
from flask import make_response
from jsonschema import RefResolver, validate, ValidationError
from typing import Union, Dict, Any
from mypy_extensions import TypedDict
from dpath.util import get
from flask import Response
from inflection import camelize


def json_api(resource, resource_class, many=False) -> Response:
    json_obj = resource_class().dump(resource, many=many).data
    response = make_response(json.dumps(json_obj))
    response.headers["Content-Type"] = "application/vnd.api+json"
    return response


def dig(obj, keypath, default=None):
    try:
        return get(obj, keypath)
    except KeyError:
        return default


Locator = TypedDict("Locator", {"type": str, "id": Union[str, int]})


def locate(locator: Locator) -> Any:
    # This doesn't actually seem to typecheck - not sure why
    klass = camelize(locator["type"])
    model_id = locator["id"]
    models = importlib.import_module("app.models")
    return getattr(models, klass).query.get(model_id)


class JSONSchemaManager:
    def __init__(self, directory: str, app=None):
        self.app = app
        self.relative_directory = directory
        self.relative_resolvers: Dict[str, RefResolver] = dict()
        self.schema_data: Dict[str, Dict] = dict()

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        directory = os.path.join(app.root_path, self.relative_directory)
        self.directory = os.path.normpath(directory)

    def validate(self, data: Union[str, dict], schema_name):
        if not self.schema_loaded(schema_name):
            self.load_json_schema(schema_name)

        json_obj = data

        if not isinstance(data, dict):
            json_obj = json.loads(data)

        return validate(
            json_obj,
            self.schema_data[schema_name],
            resolver=self.relative_resolvers[schema_name],
        )

    def is_valid(self, data: Union[str, dict], schema_name):
        try:
            validate(self, data, schema_name)
        except ValidationError:
            return False

    def schema_loaded(self, schema: str):
        return schema in self.relative_resolvers and schema in self.schema_data

    def load_json_schema(self, schema: str):
        absolute_path = os.path.join(self.directory, schema)

        with open(absolute_path) as schema_file:
            schema_data = json.loads(schema_file.read())
            self.relative_resolvers[schema] = RefResolver(
                base_uri=f"file://{self.directory}/", referrer=schema_file
            )
            self.schema_data[schema] = schema_data
