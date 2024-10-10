from .base import *  # noqa

DEBUG = False
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost").split(",")
SECRET_KEY = os.getenv("SECRET_KEY")
