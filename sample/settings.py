from pathlib import Path

import environ
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

BASE_DIR = Path(__file__).resolve().parents[1]
env = environ.Env(
    DEBUG=bool,
    ALLOWED_HOSTS=list,
    CORS_ALLOWED_ORIGINS=list,
    CORS_ALLOW_ALL_ORIGINS=bool,
)

environ.Env.read_env((BASE_DIR / ".env").as_posix())

SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django_extensions",
    "django_components",
    "django_components.safer_staticfiles",
    "django_htmx",
    # Live components (the reason we have this sample project)
    "livecomponents",
    # Local app (sample)
    "sample.myapp",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
]

ROOT_URLCONF = "sample.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
            "loaders": [
                (
                    "django.template.loaders.cached.Loader",
                    [
                        "django.template.loaders.filesystem.Loader",
                        "django.template.loaders.app_directories.Loader",
                        "django_components.template_loader.Loader",
                    ],
                )
            ],
        },
    },
]

WSGI_APPLICATION = "sample.wsgi.application"

# Database
DATABASES = {
    "default": env.db(),
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation."
        "UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Internal IPs
# Ref: https://docs.djangoproject.com/en/4.0/ref/settings/#std:setting-INTERNAL_IPS
INTERNAL_IPS = [
    "127.0.0.1",
]

# Static files (CSS, JavaScript, Images)
STATICFILES_DIRS = [
    BASE_DIR / "static",
    # To load django-components specific to myapp
    BASE_DIR / "sample/myapp/components",
]
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "static_root"

# Sentry settings
sentry_sdk.init(
    integrations=[DjangoIntegration()],
    traces_sample_rate=1.0,
    send_default_pii=True,
)
