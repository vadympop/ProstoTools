import django
import os
from django.conf import settings

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
conf = {
    'INSTALLED_APPS': [
        'core.services.database'
    ],
    'DATABASES': {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'data',
            'USER': 'root',
            'PASSWORD': 'zyzel19db',
            'HOST': '127.0.0.1',
            'PORT': '3306'
        }
    }
}

settings.configure(**conf)
django.setup()

from .database import Database