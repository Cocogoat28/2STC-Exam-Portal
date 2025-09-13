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
    "welcome_sign": "JAI HIND! Welcome to 2 Signal Training Centre Online Exam Portal",
    "copyright": "Developed by SLOG Solutions Pvt Ltd and 2STC",
    "site_brand": "Evaluation Portal",

    # Logo settings
    "site_logo": "img/logo1.png",           # top-left logo in header
    "login_logo": "img/logo1.png",          # login page logo (light bg)
    "login_logo_dark": "img/logo1.png",     # login page logo (dark bg)

    # UI tweaks
    "show_ui_builder": True,
    "custom_css": "css/admin-overrides.css",
    "custom_js": "js/admin-overrides.js",

    # ===== Jazzmin sidebar/menu customisation =====
    # Hide the raw Candidates model entry
    "hide_models": ["exams.Candidate"],
"hide_apps": ["auth"],
    # Provide the three desired links under the "exams" app section
    "custom_links": {
        "exams": [
            {
                "name": "Import Evaluation Data",
                "url": "admin:exams_candidate_import_excel",   # custom admin view
                "icon": "fas fa-file-import",
            },
            {
                "name": "Exam Evaluation",
                "url": "admin:exams_candidate_changelist",     # opens Candidates changelist
                "icon": "fas fa-clipboard-check",
            },
            {
                "name": "Export Results",
                "url": "admin:exams_export_evaluation_page",   # your export page with the button
                "icon": "fas fa-file-export",
            },
            {
                "name": "Users",                               # 👈 now appears AFTER Export Results
                "url": "admin:auth_user_changelist",          # Django's built-in User list
                "icon": "fas fa-user",
            },
        ]
    },

    # Keep the section open in sidebar for convenience (optional)
    "navigation_expanded": True,
}
DATA_UPLOAD_MAX_NUMBER_FIELDS = 100000
