import re
from datetime import datetime
from functools import wraps
from flask import request
from utils.errors import APIError


def validate_email(email: str) -> bool:
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return bool(re.match(pattern, email))


def validate_predict_payload(data: dict) -> list:
    errors = []
    required = [
        "train_number", "source_station", "destination_station",
        "journey_date", "booking_date", "class_type", "quota_type",
        "booking_wl", "current_wl", "current_rac"
    ]
    for field in required:
        if field not in data:
            errors.append(f"Missing required field: {field}")

    if errors:
        return errors

    valid_classes = {"1A", "2A", "3A", "SL", "CC", "2S", "EC"}
    if data.get("class_type") not in valid_classes:
        errors.append(f"Invalid class_type. Must be one of: {valid_classes}")

    valid_quotas = {"GN", "CK", "LD", "SS"}
    if data.get("quota_type") not in valid_quotas:
        errors.append(f"Invalid quota_type. Must be one of: {valid_quotas}")

    try:
        jd = datetime.strptime(data["journey_date"], "%Y-%m-%d")
        bd = datetime.strptime(data["booking_date"], "%Y-%m-%d")
        if bd > jd:
            errors.append("booking_date cannot be after journey_date")
    except ValueError:
        errors.append("Invalid date format. Use YYYY-MM-DD")

    if int(data.get("current_wl", 0)) > int(data.get("booking_wl", 0)):
        errors.append("current_wl cannot exceed booking_wl")

    if int(data.get("current_wl", 0)) > 0 and int(data.get("current_rac", 0)) > 0:
        errors.append("current_wl and current_rac cannot both be positive")

    return errors


def validate_json_payload(validator_func=None, required_fields=None):
    """
    Middleware decorator to automatically validate JSON payload.
    If validation fails, raises an APIError (400).
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            data = request.get_json(silent=True)
            if not data:
                raise APIError("Invalid or missing JSON body", 400)
            
            if required_fields:
                missing = [field for field in required_fields if field not in data or not data[field]]
                if missing:
                    raise APIError(f"Missing required fields: {missing}", 400)
                    
            if validator_func:
                errors = validator_func(data)
                if errors:
                    raise APIError("Validation failed", 400, payload={"details": errors})
            
            # Pass the parsed data to the route handler to avoid redundant parsing
            return f(data, *args, **kwargs)
        return decorated
    return decorator
