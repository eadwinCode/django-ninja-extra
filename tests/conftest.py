import os
import typing as t
from uuid import uuid4

import django
import pytest


def pytest_configure(config):
    from django.conf import settings

    os.environ.setdefault("NINJA_SKIP_REGISTRY", "True")

    settings.configure(
        ALLOWED_HOSTS=["*"],
        DEBUG_PROPAGATE_EXCEPTIONS=True,
        DATABASES={
            "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}
        },
        SITE_ID=1,
        SECRET_KEY="not very secret in tests",
        USE_I18N=True,
        USE_L10N=True,
        STATIC_URL="/static/",
        ROOT_URLCONF="tests.urls",
        TEMPLATES=[
            {
                "BACKEND": "django.template.backends.django.DjangoTemplates",
                "DIRS": [],
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
        ],
        MIDDLEWARE=(
            "django.middleware.security.SecurityMiddleware",
            "django.contrib.sessions.middleware.SessionMiddleware",
            "django.middleware.common.CommonMiddleware",
            "django.middleware.csrf.CsrfViewMiddleware",
            "django.contrib.auth.middleware.AuthenticationMiddleware",
            "django.contrib.messages.middleware.MessageMiddleware",
            "django.middleware.clickjacking.XFrameOptionsMiddleware",
        ),
        INSTALLED_APPS=(
            "django.contrib.admin",
            "django.contrib.auth",
            "django.contrib.contenttypes",
            "django.contrib.sessions",
            "django.contrib.sites",
            "django.contrib.staticfiles",
            "ninja_extra",
            "tests",
        ),
        PASSWORD_HASHERS=("django.contrib.auth.hashers.MD5PasswordHasher",),
        AUTHENTICATION_BACKENDS=("django.contrib.auth.backends.ModelBackend",),
        LANGUAGE_CODE="en-us",
        TIME_ZONE="UTC",
    )

    django.setup()


@pytest.fixture
def reflect_context():
    from ninja_extra.reflect import reflect

    with reflect.context():
        yield reflect


@pytest.fixture
def random_type():
    return type(f"Random{uuid4().hex[:6]}", (), {})


@pytest.fixture
def get_route_function():
    from ninja_extra.controllers.route.route_functions import RouteFunction
    from ninja_extra.reflect import reflect

    def _wrap(func: t.Callable) -> RouteFunction:
        route_object = reflect.get_metadata_or_raise_exception("ROUTE_OBJECT", func)
        route_function = reflect.get_metadata_or_raise_exception(
            "ROUTE_OBJECT_FUNCTION", route_object
        )
        return route_function

    return _wrap
