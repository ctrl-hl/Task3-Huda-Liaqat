from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from config import Config

db = SQLAlchemy()
jwt = JWTManager()
bcrypt = Bcrypt()
limiter = Limiter(key_func=get_remote_address)


@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    from app.routes.auth import is_jti_revoked

    return is_jti_revoked(jwt_payload["jti"])


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.config["JWT_BLACKLIST_ENABLED"] = True
    app.config["JWT_BLACKLIST_CHECKS"] = ["access", "refresh"]

    db.init_app(app)
    jwt.init_app(app)
    bcrypt.init_app(app)
    limiter.init_app(app)

    from app.routes.auth import auth_bp
    from app.routes.user import user_bp
    from app.utils.errors import register_error_handlers

    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    register_error_handlers(app, jwt)

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/api/health", methods=["GET"])
    def health_check():
        from app.models import User
        from app.utils.errors import success_response

        api_status = "ok"
        db_status = "connected"
        try:
            User.query.first()
        except Exception:
            db_status = "disconnected"

        message = "API is healthy" if db_status == "connected" else "API is up but database is unavailable"
        status_code = 200 if db_status == "connected" else 503

        return success_response(
            message,
            {"api": api_status, "database": db_status},
            status_code=status_code,
        )

    with app.app_context():
        from app import models  # noqa: F401

        db.create_all()

    return app
