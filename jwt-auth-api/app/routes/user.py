from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app import db
from app.models import User
from app.utils.errors import error_response, success_response
from app.utils.validators import (
    validate_profile_update_payload,
    validation_error_message,
)

user_bp = Blueprint("user", __name__, url_prefix="/api/user")


def _current_user():
    user_id = get_jwt_identity()
    return db.session.get(User, user_id)


@user_bp.route("/profile", methods=["GET"])
@jwt_required()
def get_profile():
    user = _current_user()
    if not user:
        return error_response("User not found", status_code=401)

    return success_response("Profile retrieved successfully", user.to_dict())


@user_bp.route("/profile", methods=["PUT"])
@jwt_required()
def update_profile():
    user = _current_user()
    if not user:
        return error_response("User not found", status_code=401)

    payload, errors = validate_profile_update_payload(request.get_json(silent=True))
    if errors:
        return error_response(validation_error_message(errors), status_code=400)

    if "email" in payload:
        existing = User.query.filter_by(email=payload["email"]).first()
        if existing and existing.id != user.id:
            return error_response("Email is already registered", status_code=400)
        user.email = payload["email"]

    if "username" in payload:
        existing = User.query.filter_by(username=payload["username"]).first()
        if existing and existing.id != user.id:
            return error_response("Username is already taken", status_code=400)
        user.username = payload["username"]

    db.session.commit()

    return success_response("Profile updated successfully", user.to_dict())
