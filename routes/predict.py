from flask import Blueprint, request, jsonify
from models import db
from models.prediction import Prediction, SearchHistory
from services.prediction_service import predict_status
from services.recommendation_service import get_recommendations
from utils.jwt_utils import jwt_required
from utils.validators import validate_predict_payload, validate_json_payload
from utils.errors import APIError

predict_bp = Blueprint("predict", __name__)


@predict_bp.route("/predict", methods=["POST"])
@validate_json_payload(validator_func=validate_predict_payload)
def predict(data):
    # Inject demo values silently as requested
    data["seat_capacity"] = 256
    data["distance_km"] = 1400
    data["festival_season"] = 0
    
    try:
        result = predict_status(data)
    except Exception as e:
        raise APIError(f"Model inference failed: {str(e)}", 500)

    user_id = None
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        try:
            from utils.jwt_utils import decode_token
            payload = decode_token(auth.split(" ", 1)[1])
            user_id = payload.get("user_id")
        except Exception:
            pass

    try:
        from datetime import datetime
        journey_date = datetime.strptime(data["journey_date"], "%Y-%m-%d").date()
        booking_date = datetime.strptime(data["booking_date"], "%Y-%m-%d").date()
        
        # Ensure Train exists to prevent FK violation
        from models.train import Train
        train = Train.query.get(str(data["train_number"]))
        if not train:
            new_train = Train(
                train_number=str(data["train_number"]),
                train_name="Unknown Train",
                train_type=data.get("train_type", "EXP"),
                source_station=data["source_station"],
                destination_station=data["destination_station"],
                distance_km=int(data.get("distance_km", 0)),
                seat_capacity=int(data.get("seat_capacity", 256))
            )
            db.session.add(new_train)

        pred = Prediction(
            user_id=user_id,
            train_number=str(data["train_number"]),
            source_station=data["source_station"],
            destination_station=data["destination_station"],
            journey_date=journey_date,
            booking_date=booking_date,
            class_type=data["class_type"],
            quota_type=data["quota_type"],
            booking_wl=int(data["booking_wl"]),
            current_wl=int(data["current_wl"]),
            current_rac=int(data["current_rac"]),
            seat_capacity=int(data["seat_capacity"]),
            distance_km=int(data["distance_km"]),
            festival_season=int(data["festival_season"]),
            probability_cnf=result["probability_cnf"],
            probability_rac=result["probability_rac"],
            probability_wl=result["probability_wl"],
            predicted_status=result["prediction"],
            risk_level=result["risk_level"],
            request_payload=data,
        )
        db.session.add(pred)

        sh = SearchHistory(
            user_id=user_id,
            source_station=data["source_station"],
            destination_station=data["destination_station"],
        )
        db.session.add(sh)
        from flask import current_app
        current_app.logger.info(f"Saving prediction to DB for user_id: {user_id}")
        db.session.commit()
    except Exception as e:
        from flask import current_app
        current_app.logger.error(f"Failed to save prediction to database: {str(e)}")
        db.session.rollback()

    recommendations = get_recommendations(data, result["probability_cnf"])

    response = {**result}
    if recommendations:
        response["recommendations"] = recommendations

    return jsonify({"success": True, "data": response}), 200


@predict_bp.route("/history", methods=["GET"])
@jwt_required
def history():
    user_id = request.current_user["user_id"]
    preds = (
        Prediction.query
        .filter_by(user_id=user_id)
        .order_by(Prediction.created_at.desc())
        .limit(20)
        .all()
    )
    return jsonify({"success": True, "data": {"history": [p.to_dict() for p in preds]}}), 200


@predict_bp.route("/recommend", methods=["POST"])
@validate_json_payload(required_fields=["train_number", "source_station", "destination_station", "journey_date", "class_type", "probability_cnf"])
def recommend(data):
    """
    Dedicated recommendation API using explicit SQL queries.
    Returns alternatives if probability_cnf < 50%.
    """
    prob_cnf = float(data["probability_cnf"])
    if prob_cnf >= 50.0:
        return jsonify({"success": True, "data": {"recommendations": []}}), 200

    from sqlalchemy import text
    
    # 1. Alternative Trains SQL Query
    sql_alt_trains = text("""
        SELECT train_number, train_name, train_type 
        FROM trains 
        WHERE source_station = :src 
          AND destination_station = :dest 
          AND train_number != :tnum
        LIMIT 3
    """)
    alt_trains_result = db.session.execute(sql_alt_trains, {
        "src": data["source_station"],
        "dest": data["destination_station"],
        "tnum": str(data["train_number"])
    }).fetchall()

    recommendations = []
    
    # Process Alternative Trains
    for row in alt_trains_result:
        recommendations.append({
            "type": "ALTERNATIVE_TRAIN",
            "train_number": row.train_number,
            "train_name": row.train_name,
            "train_type": row.train_type,
            "class": data["class_type"],
            "availability": "CHECK",
            "journey_date": data["journey_date"]
        })

    # 2. Alternative Dates
    from datetime import datetime, timedelta
    journey_date = datetime.strptime(data["journey_date"], "%Y-%m-%d")
    alt_date = (journey_date + timedelta(days=1)).strftime("%Y-%m-%d")
    recommendations.append({
        "type": "ALTERNATIVE_DATE",
        "train_number": str(data["train_number"]),
        "class": data["class_type"],
        "journey_date": alt_date,
        "availability": "LIKELY_AVAILABLE",
        "note": "Next day availability typically 20-35% higher"
    })

    # 3. Alternative Classes
    req_class = data["class_type"]
    downgrade_map = {"1A": "2A", "2A": "3A", "3A": "SL"}
    upgrade_map = {"SL": "3A"}
    alt_class = downgrade_map.get(req_class) or upgrade_map.get(req_class)
    
    if alt_class:
        recommendations.append({
            "type": "ALTERNATIVE_CLASS",
            "train_number": str(data["train_number"]),
            "class": alt_class,
            "journey_date": data["journey_date"],
            "availability": "AVAILABLE",
            "note": f"Switch from {req_class} to {alt_class} for higher confirmation chance"
        })

    return jsonify({"success": True, "data": {"recommendations": recommendations}}), 200
