import config
from app import routes  # register blueprints


def create_app():
    from flask import Flask
    app = Flask(__name__)
    app.config.from_object(config)

    from app.routes import register_routes
    register_routes(app)

    return app
