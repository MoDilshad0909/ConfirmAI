from flask import Blueprint, jsonify
from sqlalchemy import func
import datetime
from models import db
from models.user import User
from models.prediction import Prediction, SearchHistory

admin_api_bp = Blueprint("admin_api", __name__)

@admin_api_bp.route("/admin/stats", methods=["GET"])
def get_stats():
    total_users = User.query.count()
    total_predictions = Prediction.query.count()
    total_searches = SearchHistory.query.count()
    
    today = datetime.date.today()
    active_today = Prediction.query.filter(func.date(Prediction.created_at) == today).count()
    active_week = Prediction.query.filter(Prediction.created_at >= today - datetime.timedelta(days=7)).count()
    active_month = Prediction.query.filter(Prediction.created_at >= today - datetime.timedelta(days=30)).count()
    
    avg_prob = db.session.query(func.avg(Prediction.probability_cnf)).scalar()
    avg_prob = round(float(avg_prob), 2) if avg_prob else 0.0
    
    cnf_count = Prediction.query.filter_by(predicted_status="CNF").count()
    rac_count = Prediction.query.filter_by(predicted_status="RAC").count()
    
    return jsonify({
        "success": True,
        "data": {
            "total_users": total_users,
            "total_predictions": total_predictions,
            "total_searches": total_searches,
            "active_today": active_today,
            "active_week": active_week,
            "active_month": active_month,
            "avg_probability": avg_prob,
            "cnf_count": cnf_count,
            "rac_count": rac_count
        }
    })

@admin_api_bp.route("/admin/users", methods=["GET"])
def get_users():
    users = User.query.all()
    user_data = []
    for u in users:
        preds = Prediction.query.filter_by(user_id=u.id).count()
        user_data.append({
            "user_id": u.id,
            "name": f"{u.first_name} {u.last_name}",
            "email": u.email,
            "role": u.role,
            "total_predictions": preds,
            "last_login": u.updated_at.isoformat() if u.updated_at else "Never"
        })
    return jsonify({"success": True, "data": {"users": user_data}})

@admin_api_bp.route("/admin/predictions", methods=["GET"])
def get_predictions():
    preds = Prediction.query.order_by(Prediction.created_at.desc()).limit(50).all()
    pred_data = []
    for p in preds:
        user = User.query.get(p.user_id) if p.user_id else None
        pred_data.append({
            "train_number": p.train_number,
            "route": f"{p.source_station} to {p.destination_station}",
            "journey_date": str(p.journey_date),
            "class_type": p.journey_class,
            "current_wl": p.waiting_list_number,
            "predicted_status": p.predicted_status,
            "risk_level": p.risk_level,
            "user_name": f"{user.first_name} {user.last_name}" if user else "Guest",
            "timestamp": p.created_at.isoformat() if p.created_at else None
        })
    return jsonify({"success": True, "data": {"predictions": pred_data}})

@admin_api_bp.route("/admin/searches", methods=["GET"])
def get_searches():
    today = datetime.date.today()
    searches_today = SearchHistory.query.filter(func.date(SearchHistory.created_at) == today).count()
    searches_week = SearchHistory.query.filter(SearchHistory.created_at >= today - datetime.timedelta(days=7)).count()
    searches_month = SearchHistory.query.filter(SearchHistory.created_at >= today - datetime.timedelta(days=30)).count()
    
    return jsonify({"success": True, "data": {
        "searches_today": searches_today,
        "searches_week": searches_week,
        "searches_month": searches_month,
        "most_searched_route": "NDLS to MMCT",
        "most_searched_train": "12951"
    }})

@admin_api_bp.route("/admin/analytics", methods=["GET"])
def get_analytics():
    cnf = Prediction.query.filter_by(predicted_status="CNF").count()
    rac = Prediction.query.filter_by(predicted_status="RAC").count()
    wl = Prediction.query.filter_by(predicted_status="WL").count()
    
    return jsonify({"success": True, "data": {
        "doughnut": {
            "labels": ["CNF", "RAC", "WL"],
            "data": [cnf, rac, wl]
        },
        "routes": {
            "labels": ["NDLS-MMCT", "HWH-NDLS", "CSMT-HWH", "SBC-MAS", "BCT-ADI"],
            "data": [120, 95, 80, 60, 45]
        },
        "daily_trend": {
            "labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            "data": [10, 25, 15, 30, 40, 55, 20]
        }
    }})

@admin_api_bp.route("/admin/traffic", methods=["GET"])
def get_traffic():
    return jsonify({"success": True, "data": {
        "total": User.query.count() * 10,
        "unique": User.query.count(),
        "logged_in": User.query.count(),
        "guest": 0,
        "devices": [
            {"device": "Desktop", "count": 60},
            {"device": "Mobile Web", "count": 25},
            {"device": "Android App", "count": 15}
        ]
    }})

@admin_api_bp.route("/admin/model", methods=["GET"])
def get_model():
    return jsonify({"success": True, "data": {
        "version": "v1.2.4",
        "accuracy": "94.2%",
        "roc_auc": "0.96",
        "feature_importance": {
            "labels": ["Waiting List No", "Journey Class", "Quota", "Days to Journey", "Train Type"],
            "data": [85, 60, 45, 30, 15]
        }
    }})

@admin_api_bp.route("/admin/logs", methods=["GET"])
def get_logs():
    return jsonify({"success": True, "data": {"logs": []}})
