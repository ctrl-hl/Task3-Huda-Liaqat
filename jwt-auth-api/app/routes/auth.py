from flask import Blueprint, request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
)

from app import db, limiter
from app.models import User
from app.utils.errors import error_response, success_response
from app.utils.validators import (
    validate_login_payload,
    validate_register_payload,
    validation_error_message,
)

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

revoked_jtis = set()


def revoke_jti(jti):
    revoked_jtis.add(jti)


def is_jti_revoked(jti):
    return jti in revoked_jtis


@auth_bp.route("/register", methods=["POST"])
def register():
    payload, errors = validate_register_payload(request.get_json(silent=True))
    if errors:
        return error_response(validation_error_message(errors), status_code=400)

    if User.query.filter_by(email=payload["email"]).first():
        return error_response("Email is already registered", status_code=400)

    if User.query.filter_by(username=payload["username"]).first():
        return error_response("Username is already taken", status_code=400)

    user = User(username=payload["username"], email=payload["email"])
    user.set_password(payload["password"])
    db.session.add(user)
    db.session.commit()

    return success_response(
        "User registered successfully",
        user.to_dict(),
        status_code=201,
    )


@auth_bp.route("/login", methods=["POST"])
@limiter.limit("5 per minute")
def login():
    payload, errors = validate_login_payload(request.get_json(silent=True))
    if errors:
        return error_response(validation_error_message(errors), status_code=400)

    user = User.query.filter_by(email=payload["email"]).first()
    if not user or not user.check_password(payload["password"]):
        return error_response("Invalid email or password", status_code=401)

    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)

    return success_response(
        "Login successful",
        {
            "access_token": access_token,
            "refresh_token": refresh_token,
        },
    )


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)
    if not user:
        return error_response("User not found", status_code=401)

    access_token = create_access_token(identity=user.id)
    return success_response(
        "Access token refreshed successfully",
        {"access_token": access_token},
    )


@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    jti = get_jwt()["jti"]
    revoke_jti(jti)
    return success_response("Successfully logged out", None)
