import django
import os

from core.config import Config
from django.conf import settings

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
conf = {
    'INSTALLED_APPS': [
        'core.services.database'
    ],
    'DATABASES': {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': Config.DB_DATABASE,
            'USER': Config.DB_USER,
            'PASSWORD': Config.DB_PASSWORD,
            'HOST': Config.DB_HOST,
            'PORT': '3306',
            "OPTIONS": {'charset': 'utf8', 'use_unicode': True}
        }
    }
}

settings.configure(**conf)
django.setup()

from .database import Database