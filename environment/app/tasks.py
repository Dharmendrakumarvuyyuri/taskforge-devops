import time
from app.worker import celery_app
from app.models import OrderModel


@celery_app.task(name="tasks.process_order")
def process_order(order_id: str):
    time.sleep(1)
    OrderModel.update_status(order_id, "processed")
    return {"order_id": order_id, "status": "processed"}
