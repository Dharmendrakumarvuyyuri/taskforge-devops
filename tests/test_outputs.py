"""
Verification tests for the OrderFlow service.
Runs against /app after fixes have been applied.
Uses fakeredis so no live Redis instance is required.
"""
import sys
import json
import pytest

sys.path.insert(0, "/app")


# ---------------------------------------------------------------------------
# Module reload helper
# ---------------------------------------------------------------------------

def _drop_app_modules():
    for key in list(sys.modules.keys()):
        if key == "config" or key.startswith("app"):
            del sys.modules[key]


# ---------------------------------------------------------------------------
# config.py — attribute checks
# ---------------------------------------------------------------------------

class TestConfig:
    def setup_method(self):
        _drop_app_modules()

    def test_broker_url_attribute_exists(self):
        import config
        assert hasattr(config, "CELERY_BROKER_URL"), \
            "config is missing CELERY_BROKER_URL"

    def test_result_backend_attribute_exists(self):
        import config
        assert hasattr(config, "CELERY_RESULT_BACKEND"), \
            "config is missing CELERY_RESULT_BACKEND (check for typo)"

    def test_misspelled_attribute_removed(self):
        import config
        assert not hasattr(config, "CELERY_RESULT_BACKND"), \
            "config still defines the misspelled CELERY_RESULT_BACKND"

    def test_broker_url_is_redis(self):
        import config
        assert isinstance(config.CELERY_BROKER_URL, str) and \
            config.CELERY_BROKER_URL.startswith("redis://"), \
            f"CELERY_BROKER_URL must be a redis:// URL, got: {config.CELERY_BROKER_URL!r}"

    def test_result_backend_is_redis(self):
        import config
        assert isinstance(config.CELERY_RESULT_BACKEND, str) and \
            config.CELERY_RESULT_BACKEND.startswith("redis://"), \
            f"CELERY_RESULT_BACKEND must be a redis:// URL, got: {config.CELERY_RESULT_BACKEND!r}"

    def test_broker_url_not_none(self):
        import config
        assert config.CELERY_BROKER_URL is not None, \
            "CELERY_BROKER_URL is None — it was not assigned a value"


# ---------------------------------------------------------------------------
# app/__init__.py — circular import / factory
# ---------------------------------------------------------------------------

class TestAppFactory:
    def setup_method(self):
        _drop_app_modules()

    def test_app_package_imports_cleanly(self):
        try:
            from app import create_app  # noqa: F401
        except ImportError as exc:
            pytest.fail(f"Circular import in app/__init__.py: {exc}")

    def test_create_app_returns_flask_instance(self):
        from flask import Flask
        from app import create_app
        assert isinstance(create_app(), Flask)

    def test_create_app_callable_multiple_times(self):
        from app import create_app
        a1 = create_app()
        a2 = create_app()
        assert a1 is not a2


# ---------------------------------------------------------------------------
# app/worker.py — Celery configuration
# ---------------------------------------------------------------------------

class TestCeleryWorker:
    def setup_method(self):
        _drop_app_modules()

    def test_worker_module_imports_without_error(self):
        try:
            from app.worker import celery_app  # noqa: F401
        except AttributeError as exc:
            pytest.fail(
                f"app.worker raised AttributeError — likely reading a "
                f"misspelled config attribute: {exc}"
            )

    def test_celery_broker_is_redis(self):
        from app.worker import celery_app
        broker = celery_app.conf.broker_url
        assert broker and broker.startswith("redis://"), \
            f"Celery broker_url is {broker!r}, expected a redis:// URL"

    def test_celery_result_backend_is_redis(self):
        from app.worker import celery_app
        backend = celery_app.conf.result_backend
        assert backend and backend.startswith("redis://"), \
            f"Celery result_backend is {backend!r}, expected a redis:// URL"

    def test_celery_task_serializer_is_json(self):
        from app.worker import celery_app
        assert celery_app.conf.task_serializer == "json"

    def test_tasks_module_imports_cleanly(self):
        try:
            import app.tasks  # noqa: F401
        except Exception as exc:
            pytest.fail(f"app.tasks failed to import: {exc}")


# ---------------------------------------------------------------------------
# Flask API — functional tests via fakeredis
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client():
    try:
        import fakeredis
    except ImportError:
        pytest.skip("fakeredis not available")

    import unittest.mock as mock

    _drop_app_modules()
    from app import create_app

    fake_server = fakeredis.FakeServer()

    def _fake_redis():
        return fakeredis.FakeRedis(server=fake_server, decode_responses=True)

    with mock.patch("app.models.get_redis", side_effect=_fake_redis):
        flask_app = create_app()
        flask_app.config["TESTING"] = True
        with flask_app.test_client() as c:
            yield c


class TestHealthEndpoint:
    def test_status_200(self, client):
        r = client.get("/health")
        assert r.status_code == 200

    def test_body_correct(self, client):
        r = client.get("/health")
        assert r.get_json() == {"status": "ok"}


class TestCreateOrder:
    def test_valid_payload_returns_202(self, client):
        r = client.post("/orders",
                        data=json.dumps({"item": "bolt", "quantity": 10}),
                        content_type="application/json")
        assert r.status_code == 202

    def test_response_contains_order_id(self, client):
        r = client.post("/orders",
                        data=json.dumps({"item": "nut", "quantity": 2}),
                        content_type="application/json")
        assert "order_id" in r.get_json()

    def test_response_status_is_queued(self, client):
        r = client.post("/orders",
                        data=json.dumps({"item": "washer", "quantity": 5}),
                        content_type="application/json")
        assert r.get_json().get("status") == "queued"

    def test_missing_item_returns_400(self, client):
        r = client.post("/orders",
                        data=json.dumps({"quantity": 3}),
                        content_type="application/json")
        assert r.status_code == 400

    def test_missing_quantity_returns_400(self, client):
        r = client.post("/orders",
                        data=json.dumps({"item": "bolt"}),
                        content_type="application/json")
        assert r.status_code == 400

    def test_negative_quantity_returns_400(self, client):
        r = client.post("/orders",
                        data=json.dumps({"item": "bolt", "quantity": -1}),
                        content_type="application/json")
        assert r.status_code == 400

    def test_zero_quantity_returns_400(self, client):
        r = client.post("/orders",
                        data=json.dumps({"item": "bolt", "quantity": 0}),
                        content_type="application/json")
        assert r.status_code == 400

    def test_empty_body_returns_400(self, client):
        r = client.post("/orders", content_type="application/json")
        assert r.status_code == 400

    def test_order_id_is_unique_per_request(self, client):
        def _post():
            return client.post("/orders",
                               data=json.dumps({"item": "gear", "quantity": 1}),
                               content_type="application/json").get_json()["order_id"]
        assert _post() != _post()


class TestGetOrder:
    def _create(self, client, item="sprocket", qty=4):
        r = client.post("/orders",
                        data=json.dumps({"item": item, "quantity": qty}),
                        content_type="application/json")
        return r.get_json()["order_id"]

    def test_existing_order_returns_200(self, client):
        oid = self._create(client)
        assert client.get(f"/orders/{oid}").status_code == 200

    def test_order_data_matches_input(self, client):
        oid = self._create(client, item="cog", qty=7)
        data = client.get(f"/orders/{oid}").get_json()
        assert data["item"] == "cog"
        assert data["quantity"] == 7
        assert data["order_id"] == oid
        assert data["status"] == "queued"

    def test_unknown_id_returns_404(self, client):
        assert client.get("/orders/does-not-exist-abc123").status_code == 404

    def test_404_response_has_error_field(self, client):
        r = client.get("/orders/not-real-at-all")
        assert "error" in r.get_json()
