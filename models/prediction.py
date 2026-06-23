from models import db
from datetime import datetime


class Prediction(db.Model):
    __tablename__ = "predictions"

    prediction_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    train_number = db.Column(db.String(5), db.ForeignKey("trains.train_number", ondelete="CASCADE"), nullable=False)
    source_station = db.Column(db.String(4), nullable=False)
    destination_station = db.Column(db.String(4), nullable=False)
    journey_date = db.Column(db.Date, nullable=False, index=True)
    booking_date = db.Column(db.Date, nullable=False)
    class_type = db.Column(db.Enum("1A", "2A", "3A", "SL", "CC", "2S", "EC"), nullable=False)
    quota_type = db.Column(db.Enum("GN", "CK", "LD", "SS"), nullable=False)
    booking_wl = db.Column(db.Integer, nullable=False)
    current_wl = db.Column(db.Integer, nullable=False)
    current_rac = db.Column(db.Integer, default=0, nullable=False)
    seat_capacity = db.Column(db.Integer, nullable=False)
    distance_km = db.Column(db.Integer, nullable=False)
    festival_season = db.Column(db.Integer, default=0, nullable=False)
    probability_cnf = db.Column(db.Numeric(5, 2), nullable=False)
    probability_rac = db.Column(db.Numeric(5, 2), nullable=False)
    probability_wl = db.Column(db.Numeric(5, 2), nullable=False)
    predicted_status = db.Column(db.Enum("CNF", "RAC", "WL"), nullable=False)
    risk_level = db.Column(db.Enum("LOW", "MEDIUM", "HIGH"), nullable=False)
    actual_status = db.Column(db.Enum("CNF", "RAC", "WL"), nullable=True)
    request_payload = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "prediction_id": self.prediction_id,
            "train_number": self.train_number,
            "source_station": self.source_station,
            "destination_station": self.destination_station,
            "journey_date": str(self.journey_date),
            "class_type": self.class_type,
            "quota_type": self.quota_type,
            "booking_wl": self.booking_wl,
            "current_wl": self.current_wl,
            "current_rac": self.current_rac,
            "probability_cnf": float(self.probability_cnf),
            "probability_rac": float(self.probability_rac),
            "probability_wl": float(self.probability_wl),
            "predicted_status": self.predicted_status,
            "risk_level": self.risk_level,
            "created_at": self.created_at.isoformat(),
        }


class SearchHistory(db.Model):
    __tablename__ = "search_history"

    search_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    source_station = db.Column(db.String(4), nullable=False)
    destination_station = db.Column(db.String(4), nullable=False)
    searched_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
