import os

from django.templatetags.static import static
from django.utils.translation import gettext_lazy as _

from dotenv import load_dotenv

from pathlib import Path

# Читаем переменные окружения из .env (в корне проекта).
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'testing_secret_key')

DEBUG = True

ALLOWED_HOSTS = []

INSTALLED_APPS = [
    'unfold',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'public.apps.PublicConfig',
    'crm.apps.CrmConfig',
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

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'crm' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

LOCALE_PATHS = [
    BASE_DIR / "locale",
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'ru-RU'

TIME_ZONE = 'Europe/Moscow'

USE_I18N = True

USE_TZ = True

STATIC_URL = 'static/'

STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- Настройка темы админки Unfold ---
UNFOLD = {
    # Названия и заголовки
    "SITE_TITLE": "АвтоСервис | CRM",
    "SITE_HEADER": "АвтоСервис",
    "SITE_SUBHEADER": "Управление и статистика",
    "SITE_URL": "/",

    # Тема: "light", "dark" или "auto" (пользователь сам переключает)
    "THEME": "light",

    # admin css
    "STYLES": [
        lambda request: static("css/admin.css"),
    ],
    
    # Основной цвет (пример: оранжевый, как на вашем сайте)
    "COLORS": {
        "primary": {
            "50": "255 247 237",
            "100": "255 237 213",
            "200": "254 215 170",
            "300": "253 186 116",
            "400": "251 146 60",
            "500": "249 115 22",   # Основной тон
            "600": "234 88 12",
            "700": "194 65 12",
            "800": "154 52 18",
            "900": "120 53 15",
            "950": "67 20 7",
        },
    },
    
    # Скругление углов
    "BORDER_RADIUS": "8px",
    # Dashboard
    "DASHBOARD_CALLBACK": "crm.views.dashboard_callback",
}

# --- VK ---
VK_GROUP_TOKEN = os.getenv('VK_GROUP_TOKEN', '')
VK_GROUP_ID = os.getenv('VK_GROUP_ID', '')
VK_OWNER_ID = int(os.getenv('VK_OWNER_ID', '0'))
