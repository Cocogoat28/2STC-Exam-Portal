from pathlib import Path
import os

# BASE_DIR points to the project root (where manage.py is)
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "django-insecure-change-me"
DEBUG = True
ALLOWED_HOSTS = ["*"]

# Application definition
INSTALLED_APPS = [
    "jazzmin",  # Jazzmin must be before django.contrib.admin
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "exams",  # your custom app
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "exam_portal.urls"

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
    },
]

WSGI_APPLICATION = "exam_portal.wsgi.application"

# Database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = []

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"] if (BASE_DIR / "static").exists() else []

# Media (for storing PDFs)
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# Default PK field
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Jazzmin minimal conf
STATIC_URL = "/static/"
STATICFILES_DIRS = [
    BASE_DIR / "exam_portal" / "static",   # since your static is inside config/
]


JAZZMIN_SETTINGS = {
    "site_title": "Exam Portal",
    "site_header": "Admin Portal",
    "welcome_sign": "JAI HIND! Welcome to 2 Signal Training Centre Online Exam Portal",
    "copyright": "Developed by SLOG Solutions Pvt Ltd and 2STC",
    "site_brand": "2STC Admin Portal",

    # Logo settings
    "site_logo": "img/logo.png",           # top-left logo in header
    "login_logo": "img/logo.png",          # login page logo (light bg)
    "login_logo_dark": "img/logo.png",     # login page logo (dark bg)

    # UI tweaks
    "show_ui_builder": True,
}
