from flask import Blueprint, request, jsonify
from models import db
from models.user import User
from models.prediction import Prediction
from utils.jwt_utils import jwt_required
from utils.validators import validate_json_payload
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func

profile_bp = Blueprint("profile", __name__)

@profile_bp.route("/profile", methods=["GET"])
@jwt_required
def get_profile():
    user_id = request.current_user["user_id"]
    user = User.query.get(user_id)
    if not user:
        return jsonify({"success": False, "error": "User not found"}), 404
        
    return jsonify({
        "success": True,
        "data": {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "full_name": f"{user.first_name} {user.last_name}",
            "email": user.email,
            "role": user.role,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login": user.updated_at.isoformat() if user.updated_at else None
        }
    }), 200

@profile_bp.route("/profile/stats", methods=["GET"])
@jwt_required
def get_stats():
    user_id = request.current_user["user_id"]
    
    total_preds = Prediction.query.filter_by(user_id=user_id).count()
    cnf_preds = Prediction.query.filter_by(user_id=user_id, predicted_status="CNF").count()
    rac_preds = Prediction.query.filter_by(user_id=user_id, predicted_status="RAC").count()
    wl_preds = Prediction.query.filter_by(user_id=user_id, predicted_status="WL").count()
    
    avg_prob_cnf = db.session.query(func.avg(Prediction.probability_cnf)).filter_by(user_id=user_id).scalar()
    avg_prob_cnf = round(float(avg_prob_cnf), 2) if avg_prob_cnf else 0.0
    
    last_pred = Prediction.query.filter_by(user_id=user_id).order_by(Prediction.created_at.desc()).first()
    
    return jsonify({
        "success": True,
        "data": {
            "total_predictions": total_preds,
            "cnf_predictions": cnf_preds,
            "rac_predictions": rac_preds,
            "wl_predictions": wl_preds,
            "avg_probability_cnf": avg_prob_cnf,
            "last_prediction_date": last_pred.created_at.isoformat() if last_pred else None
        }
    }), 200

@profile_bp.route("/profile/recent-activity", methods=["GET"])
@jwt_required
def get_recent_activity():
    user_id = request.current_user["user_id"]
    
    preds = Prediction.query.filter_by(user_id=user_id).order_by(Prediction.created_at.desc()).limit(5).all()
    
    activity = [{
        "train_number": p.train_number,
        "route": f"{p.source_station} → {p.destination_station}",
        "journey_date": str(p.journey_date),
        "predicted_status": p.predicted_status,
        "prediction_date": p.created_at.isoformat()
    } for p in preds]
    
    return jsonify({
        "success": True,
        "data": {
            "recent_activity": activity
        }
    }), 200

@profile_bp.route("/profile/update", methods=["PUT"])
@jwt_required
@validate_json_payload(required_fields=["first_name", "last_name"])
def update_profile(data):
    user_id = request.current_user["user_id"]
    user = User.query.get(user_id)
    if not user:
        return jsonify({"success": False, "error": "User not found"}), 404
        
    user.first_name = data["first_name"]
    user.last_name = data["last_name"]
    db.session.commit()
    
    return jsonify({
        "success": True,
        "message": "Profile updated successfully",
        "data": {
            "first_name": user.first_name,
            "last_name": user.last_name
        }
    }), 200

@profile_bp.route("/profile/change-password", methods=["PUT"])
@jwt_required
@validate_json_payload(required_fields=["current_password", "new_password"])
def change_password(data):
    user_id = request.current_user["user_id"]
    user = User.query.get(user_id)
    if not user:
        return jsonify({"success": False, "error": "User not found"}), 404
        
    if not check_password_hash(user.password_hash, data["current_password"]):
        return jsonify({"success": False, "error": "Incorrect current password"}), 400
        
    user.password_hash = generate_password_hash(data["new_password"])
    db.session.commit()
    
    return jsonify({
        "success": True,
        "message": "Password changed successfully"
    }), 200
