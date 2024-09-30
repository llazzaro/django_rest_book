from .base import *  #noqa

DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]
SECRET_KEY = os.getenv("SECRET_KEY")

CORS_ALLOWED_ORIGINS = [
    "http://localhost",
    "http://127.0.0.1",
]
