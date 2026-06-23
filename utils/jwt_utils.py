from functools import wraps
import jwt
from flask import request, jsonify, current_app


def generate_token(user_id: int, role: str) -> str:
    from datetime import datetime, timezone
    payload = {
        "user_id": user_id,
        "role": role,
        "exp": datetime.now(timezone.utc) + current_app.config["JWT_ACCESS_TOKEN_EXPIRES"],
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, current_app.config["JWT_SECRET_KEY"], algorithm="HS256")


def decode_token(token: str) -> dict:
    return jwt.decode(token, current_app.config["JWT_SECRET_KEY"], algorithms=["HS256"])


def jwt_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401
        token = auth_header.split(" ", 1)[1]
        try:
            payload = decode_token(token)
            request.current_user = payload
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    @jwt_required
    def decorated(*args, **kwargs):
        if request.current_user.get("role") != "admin":
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)
    return decorated
