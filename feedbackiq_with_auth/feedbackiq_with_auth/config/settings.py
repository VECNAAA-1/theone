"""
config/settings.py
Application configuration settings
"""

import os
from dotenv import load_dotenv

load_dotenv()

_BASE     = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_INSTANCE = os.path.join(_BASE, "instance")


class BaseConfig:
    SECRET_KEY                 = os.getenv("SECRET_KEY", "feedbackiq-secret-2025-change-me")
    MAX_CONTENT_LENGTH         = 16 * 1024 * 1024
    UPLOAD_FOLDER              = os.getenv("UPLOAD_FOLDER", "data/uploads")
    ALLOWED_EXTENSIONS         = {"csv", "txt", "json"}
    SESSION_COOKIE_HTTPONLY    = True
    SESSION_COOKIE_SAMESITE    = "Lax"
    PERMANENT_SESSION_LIFETIME = 3600


class DevelopmentConfig(BaseConfig):
    DEBUG   = True
    TESTING = False
    DB_PATH = os.path.join(_INSTANCE, "feedbackiq_dev.db")


class ProductionConfig(BaseConfig):
    DEBUG      = False
    TESTING    = False
    SECRET_KEY = os.environ.get("SECRET_KEY")
    DB_PATH    = os.environ.get("DB_PATH", os.path.join(_INSTANCE, "feedbackiq.db"))


class TestingConfig(BaseConfig):
    DEBUG   = True
    TESTING = True
    DB_PATH = os.path.join(_INSTANCE, "feedbackiq_test.db")


config_map = {
    "development": DevelopmentConfig,
    "production":  ProductionConfig,
    "testing":     TestingConfig,
}


def get_config():
    env = os.getenv("FLASK_ENV", "development")
    return config_map.get(env, DevelopmentConfig)
