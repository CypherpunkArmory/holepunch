from app import json_schema_manager


def assert_valid_schema(data, schema_file):
    return json_schema_manager.validate(data, schema_file)
