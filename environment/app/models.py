import uuid
import json
import os
import redis

_client = None


def get_redis():
    global _client
    if _client is None:
        url = os.environ.get("REDIS_URL", "redis://redis:6379/0")
        _client = redis.Redis.from_url(url, decode_responses=True)
    return _client


class OrderModel:
    @staticmethod
    def create(item: str, quantity: int) -> str:
        order_id = str(uuid.uuid4())
        order = {
            "order_id": order_id,
            "item": item,
            "quantity": quantity,
            "status": "queued",
        }
        get_redis().set(f"order:{order_id}", json.dumps(order))
        return order_id

    @staticmethod
    def get(order_id: str):
        raw = get_redis().get(f"order:{order_id}")
        if raw is None:
            return None
        return json.loads(raw)

    @staticmethod
    def update_status(order_id: str, status: str):
        order = OrderModel.get(order_id)
        if order:
            order["status"] = status
            get_redis().set(f"order:{order_id}", json.dumps(order))
