import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
DEBUG = os.getenv("DEBUG", "True") == "True"
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "*").split(",")

INSTALLED_APPS = [
	"django.contrib.admin",
	"django.contrib.auth",
	"django.contrib.contenttypes",
	"django.contrib.sessions",
	"django.contrib.messages",
	"django.contrib.staticfiles",
	# third-party
	"rest_framework",
	"corsheaders",
	"django_celery_beat",
	"django_celery_results",
	# local apps
	"apps.common",
]

MIDDLEWARE = [
	"corsheaders.middleware.CorsMiddleware",
	"django.middleware.security.SecurityMiddleware",
	"django.contrib.sessions.middleware.SessionMiddleware",
	"django.middleware.common.CommonMiddleware",
	"django.middleware.csrf.CsrfViewMiddleware",
	"django.contrib.auth.middleware.AuthenticationMiddleware",
	"django.contrib.messages.middleware.MessageMiddleware",
	"django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "core.urls"

TEMPLATES = [
	{
		"BACKEND": "django.template.backends.django.DjangoTemplates",
		"DIRS": [BASE_DIR / "templates"],
		"APP_DIRS": True,
		"OPTIONS": {
			"context_processors": [
				"django.template.context_processors.debug",
				"django.template.context_processors.request",
				"django.contrib.auth.context_processors.auth",
				"django.contrib.messages.context_processors.messages",
			],
		},
	}
]

WSGI_APPLICATION = "core.wsgi.application"
ASGI_APPLICATION = "core.asgi.application"

DATABASES = {
	"default": {
		"ENGINE": "django.db.backends.mysql",
		"NAME": os.getenv("DB_NAME", "appdb"),
		"USER": os.getenv("DB_USER", "appuser"),
		"PASSWORD": os.getenv("DB_PASSWORD", "apppass"),
		"HOST": os.getenv("DB_HOST", "127.0.0.1"),
		"PORT": os.getenv("DB_PORT", "3306"),
		"OPTIONS": {
			"charset": "utf8mb4",
			"init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
		},
		"CONN_MAX_AGE": 60,
	}
}

CACHES = {
	"default": {
		"BACKEND": "django_redis.cache.RedisCache",
		"LOCATION": os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0"),
		"OPTIONS": {
			"CLIENT_CLASS": "django_redis.client.DefaultClient",
		}
	},
	"session": {
		"BACKEND": "django_redis.cache.RedisCache",
		"LOCATION": os.getenv("REDIS_SESSION_URL", os.getenv("REDIS_URL", "redis://127.0.0.1:6379/1")),
	}
}

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "session"

AUTH_PASSWORD_VALIDATORS = [
	{"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
	{"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
	{"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
	{"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "static"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

REST_FRAMEWORK = {
	"DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
	"PAGE_SIZE": 20,
}

CORS_ALLOW_ALL_ORIGINS = True

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0"))
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", os.getenv("REDIS_URL", "redis://127.0.0.1:6379/1"))
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_TIME_LIMIT = 30 * 60
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60
CELERY_WORKER_PREFETCH_MULTIPLIER = 1

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
