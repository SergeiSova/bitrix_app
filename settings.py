import os
from pathlib import Path
from urllib.parse import urlsplit

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

from integration_utils.bitrix24.local_settings_class import LocalSettingsClass
from integration_utils.iu_logger.classes.console_logger import ConsoleLogger

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / '.env')


def env_list(name, default=''):
    return [item.strip() for item in os.getenv(name, default).split(',') if item.strip()]


DEBUG = os.getenv('DJANGO_DEBUG', '0').strip().lower() in ('1', 'true', 'yes', 'on')

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')
BITRIX_DOMAIN = os.getenv('BITRIX_DOMAIN', '')
if not DEBUG:
    missing = [name for name, value in (('DJANGO_SECRET_KEY', SECRET_KEY), ('BITRIX_DOMAIN', BITRIX_DOMAIN)) if not value]
    if missing:
        raise ImproperlyConfigured('Задайте переменные окружения: ' + ', '.join(missing))
SECRET_KEY = SECRET_KEY or 'django-insecure-local-development-only'

ROOT_URL = os.getenv('ROOT_URL', 'http://localhost:8000').rstrip('/')
APP_HOST = urlsplit(ROOT_URL).hostname or 'localhost'
ALLOWED_HOSTS = env_list('DJANGO_ALLOWED_HOSTS') or [APP_HOST, '127.0.0.1', 'localhost']
CSRF_TRUSTED_ORIGINS = [ROOT_URL] if ROOT_URL.startswith('https://') else []

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'integration_utils.bitrix24',
    'start',
    'deals',
    'product',
    'contacts',
    'staff',
    'company',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'urls'
WSGI_APPLICATION = 'wsgi.application'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.getenv('DJANGO_DB_PATH', str(BASE_DIR / 'db.sqlite3')),
    }
}

LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Приложение открывается в iframe портала, поэтому CSRF-cookie должна работать между сайтами
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SAMESITE = 'None' if not DEBUG else 'Lax'
SESSION_COOKIE_SECURE = not DEBUG

BITRIX_WEBHOOK_AUTH = os.getenv('BITRIX_WEBHOOK_AUTH', '')
APP_SETTINGS = LocalSettingsClass(
    portal_domain=BITRIX_DOMAIN,
    app_domain=APP_HOST,
    app_name=os.getenv('BITRIX_APP_NAME', 'bitrix_app'),
    salt=os.getenv('BITRIX_APP_SALT', SECRET_KEY),
    secret_key=SECRET_KEY,
    application_bitrix_client_id=os.getenv('BITRIX_CLIENT_ID', ''),
    application_bitrix_client_secret=os.getenv('BITRIX_CLIENT_SECRET', ''),
    application_index_path='/',
)

# integration_utils импортирует логгер из модуля настроек
ilogger = ConsoleLogger()

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {'console': {'class': 'logging.StreamHandler'}},
    'loggers': {'bitrix': {'handlers': ['console'], 'level': 'INFO'}},
}
