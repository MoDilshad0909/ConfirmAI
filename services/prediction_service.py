import pickle
import numpy as np
from datetime import datetime
# pyrefly: ignore [missing-import]
from flask import current_app

_pipeline = None


def _load_pipeline():
    global _pipeline
    if _pipeline is None:
        with open(current_app.config["ML_MODEL_PATH"], "rb") as f:
            _pipeline = pickle.load(f)
    return _pipeline

def init_pipeline(app):
    with app.app_context():
        _load_pipeline()


def _compute_features(data: dict) -> dict:
    booking_date = datetime.strptime(data["booking_date"], "%Y-%m-%d")
    journey_date = datetime.strptime(data["journey_date"], "%Y-%m-%d")
    booking_days_before = max(0, (journey_date - booking_date).days)
    day_of_week = journey_date.weekday()
    month = journey_date.month

    return {
        "Train_Number": str(data["train_number"]),
        "Train_Type": data.get("train_type", "SF"),
        "Source_Station": data["source_station"],
        "Destination_Station": data["destination_station"],
        "Class_Type": data["class_type"],
        "Quota_Type": data["quota_type"],
        "Seat_Capacity": int(data["seat_capacity"]),
        "Booking_WL": int(data["booking_wl"]),
        "Current_WL": int(data["current_wl"]),
        "Current_RAC": int(data["current_rac"]),
        "Distance_KM": int(data["distance_km"]),
        "Festival_Season": int(data["festival_season"]),
        "Booking_Days_Before": booking_days_before,
        "Day_Of_Week": day_of_week,
        "Month": month,
    }


def predict_status(data: dict) -> dict:
    import pandas as pd

    pipeline = _load_pipeline()
    preprocessor = pipeline["preprocessor"]
    model = pipeline["model"]
    features = pipeline["features"]
    inv_map = pipeline["inverse_target_map"]

    feat_dict = _compute_features(data)

    log_booking_wl = np.log1p(feat_dict["Booking_WL"])
    log_current_wl = np.log1p(feat_dict["Current_WL"])
    dow = feat_dict["Day_Of_Week"]
    month = feat_dict["Month"]

    row = {
        "Seat_Capacity": feat_dict["Seat_Capacity"],
        "Log_Booking_WL": log_booking_wl,
        "Log_Current_WL": log_current_wl,
        "Current_RAC": feat_dict["Current_RAC"],
        "Distance_KM": feat_dict["Distance_KM"],
        "Booking_Days_Before": feat_dict["Booking_Days_Before"],
        "Festival_Season": feat_dict["Festival_Season"],
        "Class_Type": feat_dict["Class_Type"],
        "Quota_Type": feat_dict["Quota_Type"],
        "Train_Type": feat_dict["Train_Type"],
        "Train_Number": feat_dict["Train_Number"],
        "Source_Station": feat_dict["Source_Station"],
        "Destination_Station": feat_dict["Destination_Station"],
        "Day_Of_Week_sin": np.sin(2 * np.pi * dow / 7.0),
        "Day_Of_Week_cos": np.cos(2 * np.pi * dow / 7.0),
        "Month_sin": np.sin(2 * np.pi * month / 12.0),
        "Month_cos": np.cos(2 * np.pi * month / 12.0),
    }

    df = pd.DataFrame([row])[features]
    X_proc = preprocessor.transform(df)
    proba = model.predict_proba(X_proc)[0]

    # Order: WL=0, RAC=1, CNF=2
    prob_wl = round(float(proba[0]) * 100, 2)
    prob_rac = round(float(proba[1]) * 100, 2)
    prob_cnf = round(float(proba[2]) * 100, 2)

    predicted_class = inv_map[int(np.argmax(proba))]

    if prob_cnf >= 60:
        risk = "LOW"
    elif prob_cnf >= 30:
        risk = "MEDIUM"
    else:
        risk = "HIGH"

    return {
        "prediction": predicted_class,
        "probability_cnf": prob_cnf,
        "probability_rac": prob_rac,
        "probability_wl": prob_wl,
        "risk_level": risk,
        "booking_days_before": feat_dict["Booking_Days_Before"],
    }
