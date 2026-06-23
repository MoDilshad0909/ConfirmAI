import os
from datetime import datetime
from app import create_app
from models import db
from models.prediction import Prediction, SearchHistory

app = create_app()
with app.app_context():
    try:
        data = {
            "train_number": "12345",
            "source_station": "NDLS",
            "destination_station": "MMCT",
            "journey_date": "2026-06-25",
            "booking_date": "2026-06-23",
            "class_type": "SL",
            "quota_type": "GN",
            "booking_wl": 10,
            "current_wl": 5,
            "current_rac": 0,
            "seat_capacity": 256,
            "distance_km": 1400,
            "festival_season": 0,
        }
        
        journey_date = datetime.strptime(data["journey_date"], "%Y-%m-%d").date()
        booking_date = datetime.strptime(data["booking_date"], "%Y-%m-%d").date()
        
        pred = Prediction(
            user_id=1,
            train_number=str(data["train_number"]),
            source_station=data["source_station"],
            destination_station=data["destination_station"],
            journey_date=data["journey_date"],
            booking_date=data["booking_date"],
            class_type=data["class_type"],
            quota_type=data["quota_type"],
            booking_wl=int(data["booking_wl"]),
            current_wl=int(data["current_wl"]),
            current_rac=int(data["current_rac"]),
            seat_capacity=int(data["seat_capacity"]),
            distance_km=int(data["distance_km"]),
            festival_season=int(data["festival_season"]),
            probability_cnf=80.0,
            probability_rac=10.0,
            probability_wl=10.0,
            predicted_status="CNF",
            risk_level="LOW",
            request_payload=data,
        )
        db.session.add(pred)
        sh = SearchHistory(
            user_id=1,
            source_station=data["source_station"],
            destination_station=data["destination_station"],
        )
        db.session.add(sh)
        db.session.commit()
        print("Insert successful!")
    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        print(f"Insert failed: {e}")
