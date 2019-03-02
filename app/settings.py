import os


class Config(object):
    """
    Common configurations
    """

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    CONSUL_HOST = os.getenv("CONSUL_HOST")


class TestConfig(Config):
    """
    Testing Configuration
    """

    RQ_REDIS_URL = "redis://redis:6379"
    MAIL_SERVER = "mail"
    MAIL_PORT = 1025
    MAIL_USE_TLS = False
    MAIL_USERNAME = ""
    MAIL_PASSWORD = ""
    MAIL_DEFAULT_SENDER = "noreply@holepunch.io"

    TESTING = True
    SQLALCHEMY_DATABASE_URI = f'postgresql://{os.getenv("DATABASE_URL")}/holepunch_test'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    BASE_SERVICE_URL = os.environ.get("BASE_SERVICE_URL", default="configfailed")


class DevelopmentConfig(Config):
    """
    Development Configuration
    """

    DEBUG = True
    TESTING = False
    SQLALCHEMY_ECHO = True
    SQLALCHEMY_DATABASE_URI = (
        f'postgresql://{os.getenv("DATABASE_URL")}/holepunch_development'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    BASE_SERVICE_URL = os.environ.get("BASE_SERVICE_URL", default="configfailed")
    RQ_REDIS_URL = "redis://redis:6379"
    MAIL_SERVER = "mail"
    MAIL_PORT = 1025
    MAIL_USE_TLS = False
    MAIL_USERNAME = ""
    MAIL_PASSWORD = ""
    MAIL_DEFAULT_SENDER = "noreply@holepunch.io"


class ProductionConfig(Config):
    """
    Production Configuration
    """

    DEBUG = False
    SQLALCHEMY_DATABASE_URI = (
        f'postgresql://{os.getenv("DATABASE_URL")}/holepunch_production'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    BASE_SERVICE_URL = os.environ.get("BASE_SERVICE_URL", default="configfailed")
    MAIL_SERVER = "email-smtp.us-west-2.amazonaws.com"
    MAIL_PORT = 465
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = "noreply@holepunch.io"
    ROLLBAR_TOKEN = os.environ.get("ROLLBAR_TOKEN")
    RQ_REDIS_URL = os.environ.get("RQ_REDIS_URL")


app_config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "test": TestConfig,
}
