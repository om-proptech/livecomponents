from pathlib import Path

import environ

# BASE_DIR is "$PROJECT_ROOT/example"
BASE_DIR = Path(__file__).resolve().parents[1]
env = environ.Env(
    DEBUG=bool,
    ALLOWED_HOSTS=list,
    CORS_ALLOWED_ORIGINS=list,
    CORS_ALLOW_ALL_ORIGINS=bool,
    REDIS_URL=(str, "redis://localhost:6379/0"),
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
    "django_components",
    "django_components.safer_staticfiles",
    "django_htmx",
    # Live components (the reason we have this sample project)
    "livecomponents",
    # Local apps (samples)
    "counters",
    "coffee",
    "modals",
    "registration",
    "uploads",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
]

ROOT_URLCONF = "project.urls"

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

WSGI_APPLICATION = "project.wsgi.application"

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
USE_TZ = True

# Internal IPs
# Ref: https://docs.djangoproject.com/en/4.0/ref/settings/#std:setting-INTERNAL_IPS
INTERNAL_IPS = [
    "127.0.0.1",
]

# Static files (CSS, JavaScript, Images)
STATICFILES_DIRS = [
    # To load django-components specific to apps
    BASE_DIR / "project/../counters/components",
    BASE_DIR / "project/../coffee/components",
    BASE_DIR / "project/../modals/components",
    BASE_DIR / "project/../registration/components",
    BASE_DIR / "project/../uploads/components",
]
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "static_root"


# Custom logging settings
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname}: {module}: {message}",
            "style": "{",
            "datefmt": "%d/%b/%Y %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "livecomponents": {
            "handlers": ["console"],
            "level": "DEBUG",
        },
    },
}


# Live components settings
LIVECOMPONENTS = {
    "state_serializer": {
        "cls": "livecomponents.manager.serializers.PickleStateSerializer",
        "config": {},
    },
    "state_store": {
        # You can also use "MemoryStateStore" for tests.
        "cls": "livecomponents.manager.stores.RedisStateStore",
        # See "RedisStateStore" constructor for config options.
        "config": {
            "redis_url": env("REDIS_URL"),
        },
    },
    "state_manager": {
        "cls": "livecomponents.manager.manager.StateManager",
        "config": {},
    },
}
