from flask import Blueprint, jsonify
from services.auth_service import register_user, login_user
from utils.jwt_utils import jwt_required
from utils.validators import validate_email, validate_json_payload
from utils.errors import APIError
from models.user import User
from flask import request

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
@validate_json_payload(required_fields=["email", "password", "first_name", "last_name"])
def register(data):
    if not validate_email(data["email"]):
        raise APIError("Invalid email format", 400)

    if len(data["password"]) < 6:
        raise APIError("Password must be at least 6 characters", 400)

    user, err = register_user(data)
    if err:
        raise APIError(err, 409)

    return jsonify({
        "success": True,
        "message": "User registered successfully", 
        "data": {"user": user.to_dict()}
    }), 201


@auth_bp.route("/login", methods=["POST"])
@validate_json_payload(required_fields=["email", "password"])
def login(data):
    user, token, err = login_user(data["email"], data["password"])
    if err:
        raise APIError(err, 401)

    return jsonify({
        "success": True,
        "message": "Login successful",
        "data": {
            "token": token,
            "user": user.to_dict()
        }
    }), 200


@auth_bp.route("/profile", methods=["GET"])
@jwt_required
def profile():
    user_id = request.current_user["user_id"]
    user = User.query.get(user_id)
    if not user:
        raise APIError("User not found", 404)
    return jsonify({"success": True, "data": {"user": user.to_dict()}}), 200
