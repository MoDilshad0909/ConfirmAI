import pickle
import numpy as np
from datetime import datetime
from flask import current_app

_pipeline = None


def init_pipeline(app):
    """Pre-load the ML model globally during app startup to avoid cold-start latency."""
    global _pipeline
    if _pipeline is None:
        with open(app.config["ML_MODEL_PATH"], "rb") as f:
            _pipeline = pickle.load(f)
        app.logger.info("XGBoost Model loaded successfully.")

def _get_pipeline():
    global _pipeline
    if _pipeline is None:
        init_pipeline(current_app)
    return _pipeline


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
        "Seat_Capacity": int(data.get("seat_capacity", 256)),
        "Booking_WL": int(data["booking_wl"]),
        "Current_WL": int(data["current_wl"]),
        "Current_RAC": int(data["current_rac"]),
        "Distance_KM": int(data.get("distance_km", 1400)),
        "Festival_Season": int(data.get("festival_season", 0)),
        "Booking_Days_Before": booking_days_before,
        "Day_Of_Week": day_of_week,
        "Month": month,
    }


def _generate_explanation(feat_dict: dict, predicted_class: str) -> dict:
    positives = []
    negatives = []

    if predicted_class == "CNF":
        if feat_dict["Booking_Days_Before"] > 60:
            positives.append(f"Booking {feat_dict['Booking_Days_Before']} days earlier")
        if feat_dict["Current_WL"] < 20:
            positives.append("Low Current WL")
        if feat_dict["Seat_Capacity"] > 800:
            positives.append("High Capacity")
        if feat_dict["Festival_Season"] == 1:
            negatives.append("Festival Season (High Demand)")
        elif feat_dict["Current_WL"] > 0:
            negatives.append("Already in Waitlist")
            
        return {"why_positive": positives, "why_negative": negatives, "positive_label": "Why CNF?", "negative_label": "Why not WL?"}
        
    elif predicted_class == "WL":
        if feat_dict["Festival_Season"] == 1:
            positives.append("Festival Season Rush")
        if feat_dict["Current_WL"] > 50:
            positives.append("High Current WL")
        if feat_dict["Booking_Days_Before"] < 10:
            positives.append("Last Minute Booking")
        if feat_dict["Seat_Capacity"] > 1000:
            negatives.append("High Train Capacity")
            
        return {"why_positive": positives, "why_negative": negatives, "positive_label": "Why WL?", "negative_label": "Why not CNF?"}

    else: # RAC
        if feat_dict["Current_RAC"] > 0:
            positives.append("Already in RAC")
        if feat_dict["Booking_Days_Before"] > 30:
            positives.append("Decent advance booking")
        if feat_dict["Festival_Season"] == 1:
            negatives.append("Festival Season")
            
        return {"why_positive": positives, "why_negative": negatives, "positive_label": "Why RAC?", "negative_label": "Why not CNF?"}

def predict_status(data: dict) -> dict:
    import pandas as pd

    pipeline = _get_pipeline()
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
        
    explanation = _generate_explanation(feat_dict, predicted_class)

    return {
        "prediction": predicted_class,
        "probability_cnf": prob_cnf,
        "probability_rac": prob_rac,
        "probability_wl": prob_wl,
        "risk_level": risk,
        "booking_days_before": feat_dict["Booking_Days_Before"],
        "explanation": explanation
    }
