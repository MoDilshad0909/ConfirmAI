from app import create_app
from models import db
from models.prediction import Prediction
from models.train import Train
from sqlalchemy import text
from datetime import datetime

app = create_app()
with app.app_context():
    try:
        train = Train.query.first()
        tnum = train.train_number if train else "12345"
        
        j_date = datetime.strptime("2026-07-01", "%Y-%m-%d").date()
        b_date = datetime.strptime("2026-06-01", "%Y-%m-%d").date()

        pred = Prediction(
            train_number=tnum,
            source_station="NDLS",
            destination_station="MMCT",
            journey_date=j_date,
            booking_date=b_date,
            class_type="3A",
            quota_type="GN",
            booking_wl=10,
            current_wl=5,
            current_rac=0,
            seat_capacity=100,
            distance_km=1000,
            probability_cnf=50.0,
            probability_rac=20.0,
            probability_wl=30.0,
            predicted_status="WL",
            risk_level="HIGH"
        )
        db.session.add(pred)
        db.session.commit()
        print("Prediction saved successfully!")
    except Exception as e:
        db.session.rollback()
        print(f"Exception when saving: {e}")
