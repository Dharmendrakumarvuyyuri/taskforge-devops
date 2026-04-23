#!/usr/bin/env bash
set -e

# Fix 1 & 2: config.py — set CELERY_BROKER_URL correctly and fix misspelled CELERY_RESULT_BACKND
python3 - <<'PYEOF'
path = "/app/config.py"
content = """import os

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"

REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")

CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
"""
open(path, "w").write(content)
print("config.py patched")
PYEOF

# Fix 3: app/__init__.py — remove top-level circular import of routes
python3 - <<'PYEOF'
path = "/app/app/__init__.py"
content = """import config


def create_app():
    from flask import Flask
    app = Flask(__name__)
    app.config.from_object(config)

    from app.routes import register_routes
    register_routes(app)

    return app
"""
open(path, "w").write(content)
print("app/__init__.py patched")
PYEOF

# Fix 4: app/worker.py — read the correctly-spelled CELERY_RESULT_BACKEND
python3 - <<'PYEOF'
path = "/app/app/worker.py"
content = """from celery import Celery
import config


def make_celery():
    celery = Celery(
        "orderflow",
        broker=config.CELERY_BROKER_URL,
        backend=config.CELERY_RESULT_BACKEND,
    )
    celery.conf.update(
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="UTC",
        enable_utc=True,
    )
    return celery


celery_app = make_celery()
"""
open(path, "w").write(content)
print("app/worker.py patched")
PYEOF

echo "All fixes applied."
