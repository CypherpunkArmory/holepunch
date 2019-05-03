import os


class Config(object):
    """
    Common configurations
    """

    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
    CONSUL_HOST = os.environ.get("CONSUL_HOST")


class TestConfig(Config):
    """
    Testing Configuration
    """

    RQ_REDIS_URL = "redis://redis:6379"
    # RQ_ASYNC = False
    MAIL_SERVER = "mail"
    MAIL_PORT = 1025
    MAIL_USE_TLS = False
    MAIL_USERNAME = ""
    MAIL_PASSWORD = ""
    MAIL_DEFAULT_SENDER = "noreply@holepunch.io"

    TESTING = True

    SQLALCHEMY_DATABASE_URI = (
        f'postgresql://{os.environ.get("DATABASE_URL")}/holepunch_test'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    BASE_SERVICE_URL = os.environ.get("BASE_SERVICE_URL", default="configfailed")
    SEA_HOST = os.environ.get("SEA_HOST", default="nomad")
    SERVER_NAME = os.environ.get("SERVER_NAME", default="configfailed")
    DNS_ADDR = os.environ.get("DNS_ADDR", default="127.0.0.53")

    MIN_CALVER = os.environ.get("MIN_CALVER")

    PRESERVE_CONTEXT_ON_EXCEPTION = False


class DevelopmentConfig(Config):
    """
    Development Configuration
    """

    DEBUG = True
    TESTING = False

    RQ_REDIS_URL = "redis://redis:6379"

    MAIL_SERVER = "mail"
    MAIL_PORT = 1025
    MAIL_USE_TLS = False
    MAIL_USERNAME = ""
    MAIL_PASSWORD = ""
    MAIL_DEFAULT_SENDER = "noreply@holepunch.io"

    SQLALCHEMY_ECHO = True
    SQLALCHEMY_DATABASE_URI = (
        f'postgresql://{os.environ.get("DATABASE_URL")}/holepunch_development'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    BASE_SERVICE_URL = os.environ.get("BASE_SERVICE_URL", default="configfailed")
    SEA_HOST = os.environ.get("SEA_HOST", default="0.0.0.0")
    DNS_ADDR = os.environ.get("DNS_ADDR", default="172.17.0.1")
    SERVER_NAME = os.environ.get("SERVER_NAME", default="configfailed")

    MIN_CALVER = os.environ.get("MIN_CALVER")


class ProductionConfig(Config):
    """
    Production Configuration
    """

    DEBUG = False

    ROLLBAR_TOKEN = os.environ.get("ROLLBAR_TOKEN")

    RQ_REDIS_URL = os.environ.get("RQ_REDIS_URL")

    MAIL_SERVER = "email-smtp.us-west-2.amazonaws.com"
    MAIL_PORT = 465
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = "noreply@holepunch.io"

    SQLALCHEMY_DATABASE_URI = (
        f'postgresql://{os.environ.get("DATABASE_URL")}/holepunch_production'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    BASE_SERVICE_URL = os.environ.get("BASE_SERVICE_URL", default="configfailed")
    SEA_HOST = os.environ.get("SEA_HOST", default="nomad")
    DNS_ADDR = os.environ.get("DNS_ADDR", default="127.0.0.53")
    SERVER_NAME = os.environ.get("SERVER_NAME", default="configfailed")

    MIN_CALVER = os.environ.get("MIN_CALVER")


app_config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "test": TestConfig,
}
