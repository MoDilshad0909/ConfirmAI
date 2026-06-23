from flask import Blueprint, jsonify
from models.train import Train
from models.station import Station
from utils.errors import APIError
from services.irctc_api_client import IndianRailAPIClient

metadata_bp = Blueprint("metadata", __name__)


@metadata_bp.route("/stations", methods=["GET"])
def get_stations():
    stations = Station.query.order_by(Station.station_name.asc()).all()
    if not stations:
        # Fallback to defaults if not seeded yet
        return jsonify({"success": True, "data": {"stations": [
            {"code": "NDLS", "name": "New Delhi"},
            {"code": "CSMT", "name": "Mumbai CST"}
        ]}}), 200
        
    return jsonify({
        "success": True, 
        "data": {
            "stations": [s.to_dict() for s in stations]
        }
    }), 200


@metadata_bp.route("/train_info/<train_number>", methods=["GET"])
def get_train_info(train_number):
    client = IndianRailAPIClient()
    schedule = client.get_train_schedule(train_number)
    live_status = client.get_live_train_status(train_number, "today")
    
    if not schedule["success"]:
        raise APIError("Train not found", 404)
    
    train_data = schedule["data"]
    train_data["live_status"] = live_status.get("data", {})
    
    return jsonify({
        "success": True, 
        "data": {
            "train": train_data
        }
    }), 200
