from flask import Blueprint, request, jsonify
from app.models import OrderModel

orders_bp = Blueprint("orders", __name__)


def register_routes(app):
    app.register_blueprint(orders_bp)


@orders_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


@orders_bp.route("/orders", methods=["POST"])
def create_order():
    data = request.get_json(silent=True)
    if not data or "item" not in data or "quantity" not in data:
        return jsonify({"error": "Missing required fields: item, quantity"}), 400

    if not isinstance(data["quantity"], int) or data["quantity"] <= 0:
        return jsonify({"error": "quantity must be a positive integer"}), 400

    order_id = OrderModel.create(data["item"], data["quantity"])

    try:
        from app.tasks import process_order
        process_order.delay(order_id)
    except Exception:
        pass

    return jsonify({"order_id": order_id, "status": "queued"}), 202


@orders_bp.route("/orders/<order_id>", methods=["GET"])
def get_order(order_id):
    order = OrderModel.get(order_id)
    if order is None:
        return jsonify({"error": "Order not found"}), 404
    return jsonify(order), 200
