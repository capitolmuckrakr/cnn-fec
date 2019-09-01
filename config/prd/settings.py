import os

from config.dev.settings import *

DEBUG = False

WSGI_APPLICATION = 'config.prd.app.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ.get('DB_NAME', 'fec_prd'),
        'USER': os.environ.get('DB_USER', 'fec_prd'),
        'PASSWORD': os.environ.get('DB_PASSWORD', None),
        'HOST': os.environ.get('DB_HOST', None),
        'PORT': os.environ.get('DB_PORT', 5432),
    }
}

ALLOWED_HOSTS = ['*']

AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID', None)
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', None)
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME', None)
AWS_STATIC_LOCATION = os.environ.get('AWS_STATIC_LOCATION', None)
AWS_LOCATION = AWS_STATIC_LOCATION
AWS_MEDIA_LOCATION = os.environ.get('AWS_MEDIA_LOCATION', None)
AWS_DEFAULT_ACL = 'public-read'
AWS_QUERYSTRING_AUTH = False
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=600',
}

STATICFILES_LOCATION = AWS_STATIC_LOCATION
MEDIAFILES_LOCATION = AWS_MEDIA_LOCATION

STATICFILES_STORAGE = 'utils.custom_storages.StaticStorage'
DEFAULT_FILE_STORAGE = 'utils.custom_storages.MediaStorage'

STATIC_URL = f"https://s3.amazonaws.com/{AWS_STORAGE_BUCKET_NAME}/{AWS_STATIC_LOCATION}/"
MEDIA_URL = f"https://s3.amazonaws.com/{AWS_STORAGE_BUCKET_NAME}/{AWS_MEDIA_LOCATION}/"
