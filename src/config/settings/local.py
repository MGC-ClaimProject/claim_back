import os
import random

from config.settings.base import *
from dotenv import dotenv_values

DEBUG = True

ENV = dotenv_values("../local.env")
SECRET_KEY = ENV.get(
    "DJANGO_SECRET_KEY",
    "".join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()?", k=50)),
)

ALLOWED_HOSTS = []

# Database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "HOST": ENV.get("POSTGRES_HOST", "localhost"),
        "USER": ENV.get("POSTGRES_USER", "postgres"),
        "PASSWORD": ENV.get("POSTGRES_PASSWORD", "postgres"),
        "NAME": ENV.get("POSTGRES_DBNAME", "postgres"),
        "PORT": ENV.get("POSTGRES_PORT", 5432),
    }
}

# Static
STATIC_URL = "static/"
STATIC_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / ".static_root"

# Media
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# OAuth
NAVER_CLIENT_ID = ENV.get("NAVER_CLIENT_ID", "")
NAVER_CLIENT_SECRET = ENV.get("NAVER_CLIENT_SECRET", "")

KAKAO_CLIENT_ID = ENV.get("KAKAO_CLIENT_ID", "")
KAKAO_CLIENT_SECRET = ENV.get("KAKAO_CLIENT_SECRET", "")

GOOGLE_CLIENT_ID = ENV.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = ENV.get("GOOGLE_CLIENT_SECRET", "")
