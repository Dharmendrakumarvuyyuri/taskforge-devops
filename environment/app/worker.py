from celery import Celery
import config


def make_celery():
    celery = Celery(
        "orderflow",
        broker=config.CELERY_BROKER_URL,
        backend=config.CELERY_RESULT_BACKND,
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
