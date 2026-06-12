from flask import jsonify


def success_response(message, data=None, status_code=200):
    return (
        jsonify({"status": "success", "message": message, "data": data}),
        status_code,
    )


def error_response(message, data=None, status_code=400):
    return (
        jsonify({"status": "error", "message": message, "data": data}),
        status_code,
    )


def register_error_handlers(app, jwt_manager):
    @app.errorhandler(400)
    def bad_request(error):
        message = getattr(error, "description", None) or "Bad request"
        return error_response(message, status_code=400)

    @app.errorhandler(404)
    def not_found(error):
        return error_response("Route not found", status_code=404)

    @app.errorhandler(422)
    def unprocessable_entity(error):
        message = getattr(error, "description", None) or "Unprocessable entity"
        return error_response(message, status_code=422)

    @app.errorhandler(429)
    def too_many_requests(error):
        return error_response(
            "Too many requests. Please try again later.",
            status_code=429,
        )

    @app.errorhandler(500)
    def internal_server_error(error):
        return error_response("Internal server error", status_code=500)

    @jwt_manager.unauthorized_loader
    def missing_token_callback(error):
        return error_response("Missing or invalid authorization token", status_code=401)

    @jwt_manager.invalid_token_loader
    def invalid_token_callback(error):
        return error_response(f"Invalid token: {error}", status_code=422)

    @jwt_manager.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return error_response("Token has expired", status_code=401)

    @jwt_manager.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return error_response("Token has been revoked", status_code=401)

    @jwt_manager.needs_fresh_token_loader
    def needs_fresh_token_callback(jwt_header, jwt_payload):
        return error_response("Fresh token required", status_code=401)
