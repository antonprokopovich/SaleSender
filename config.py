import os

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())


class Config:
    DEBUG = False

    REST_HOST = "0.0.0.0"
    REST_PORT = 8080


class EnvironmentConfig(Config):
    def __init__(self):
        false_liters = ('0', "False", "false")
        self.DEBUG = os.environ.get("DEBUG", str(Config.DEBUG)) not in false_liters

        self.REST_HOST = os.environ.get("REST_HOST", Config.REST_HOST)
        self.REST_PORT = int(os.environ.get("REST_PORT", Config.REST_PORT))

        self.TG_API_ID = os.environ.get("TG_API_ID", "")
        self.TG_API_HASH = os.environ.get("TG_API_HASH", "")
