from marshmallow_jsonapi import Schema, fields
from functools import partial
import inflection

drinkingCamel = partial(inflection.camelize, uppercase_first_letter=False)


class TunnelSchema(Schema):
    class Meta:
        type_ = "tunnel"
        strict = True
        inflect = drinkingCamel

    id = fields.Str()
    port = fields.List(fields.Str())
    ssh_port = fields.Str()
    ip_address = fields.Str()

    subdomain = fields.Relationship(
        "/subdomains/{subdomain_id}",
        related_url_kwargs={"subdomain_id": "<subdomain_id>"},
        include_resource_linkage=True,
        type_="subdomain",
    )


class SubdomainSchema(Schema):
    class Meta:
        type_ = "subdomain"
        strict = True
        inflect = drinkingCamel

    id = fields.Str()
    name = fields.Str()
    in_use = fields.Boolean()
    reserved = fields.Boolean()


class UserSchema(Schema):
    class Meta:
        type_ = "user"
        strict = True
        inflect = drinkingCamel

    id = fields.Str()
    email = fields.Str()
    tier = fields.Str()
    confirmed = fields.Boolean()


class ErrorSchema(Schema):
    class Meta:
        type_ = "error"
        strict = True
        inflect = drinkingCamel

    id = fields.Str()
    status = fields.Str()
    title = fields.Str()
    detail = fields.Str()
    source = fields.Str()
    code = fields.Str()
    backtrace = fields.List(fields.Str())
