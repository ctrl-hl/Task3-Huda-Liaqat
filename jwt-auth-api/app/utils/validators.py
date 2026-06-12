import re

USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_]{3,30}$")
EMAIL_PATTERN = re.compile(
    r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
)


def _is_missing(value):
    return value is None or (isinstance(value, str) and not value.strip())


def validate_username(username):
    if _is_missing(username):
        return False, "Username is required"
    username = username.strip()
    if not USERNAME_PATTERN.match(username):
        return (
            False,
            "Username must be 3-30 characters and contain only letters, "
            "numbers, and underscores",
        )
    return True, username


def validate_email(email):
    if _is_missing(email):
        return False, "Email is required"
    email = email.strip().lower()
    if not EMAIL_PATTERN.match(email):
        return False, "Email must be a valid email address"
    return True, email


def validate_password(password):
    if _is_missing(password):
        return False, "Password is required"
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number"
    return True, password


def validate_register_payload(data):
    if data is None or not isinstance(data, dict):
        return None, "Request body must be valid JSON"

    errors = {}
    for field in ("username", "email", "password"):
        if field not in data or _is_missing(data.get(field)):
            errors[field] = f"{field.capitalize()} is required"

    if errors:
        return None, errors

    valid, result = validate_username(data["username"])
    if not valid:
        errors["username"] = result
    else:
        username = result

    valid, result = validate_email(data["email"])
    if not valid:
        errors["email"] = result
    else:
        email = result

    valid, result = validate_password(data["password"])
    if not valid:
        errors["password"] = result
    else:
        password = result

    if errors:
        return None, errors

    return {"username": username, "email": email, "password": password}, None


def validate_login_payload(data):
    if data is None or not isinstance(data, dict):
        return None, "Request body must be valid JSON"

    errors = {}
    for field in ("email", "password"):
        if field not in data or _is_missing(data.get(field)):
            errors[field] = f"{field.capitalize()} is required"

    if errors:
        return None, errors

    valid, result = validate_email(data["email"])
    if not valid:
        errors["email"] = result
    else:
        email = result

    password = data["password"]

    if errors:
        return None, errors

    return {"email": email, "password": password}, None


def validate_profile_update_payload(data):
    if data is None or not isinstance(data, dict):
        return None, "Request body must be valid JSON"

    if "username" not in data and "email" not in data:
        return None, "At least one of username or email must be provided"

    errors = {}
    payload = {}

    if "username" in data:
        if _is_missing(data["username"]):
            errors["username"] = "Username cannot be empty"
        else:
            valid, result = validate_username(data["username"])
            if not valid:
                errors["username"] = result
            else:
                payload["username"] = result

    if "email" in data:
        if _is_missing(data["email"]):
            errors["email"] = "Email cannot be empty"
        else:
            valid, result = validate_email(data["email"])
            if not valid:
                errors["email"] = result
            else:
                payload["email"] = result

    if errors:
        return None, errors

    if not payload:
        return None, "At least one of username or email must be provided"

    return payload, None


def validation_error_message(errors):
    if isinstance(errors, dict):
        return "; ".join(f"{key}: {value}" for key, value in errors.items())
    return str(errors)
