from models import db
from datetime import datetime


class Train(db.Model):
    __tablename__ = "trains"

    train_number = db.Column(db.String(5), primary_key=True)
    train_name = db.Column(db.String(100), nullable=False)
    train_type = db.Column(db.Enum("RAJ", "SHT", "SF", "EXP"), nullable=False)
    source_station = db.Column(db.String(4), nullable=False, index=True)
    destination_station = db.Column(db.String(4), nullable=False, index=True)
    distance_km = db.Column(db.Integer, nullable=False)
    seat_capacity = db.Column(db.Integer, nullable=False, default=256)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    predictions = db.relationship("Prediction", backref="train", lazy="dynamic")

    def to_dict(self):
        return {
            "train_number": self.train_number,
            "train_name": self.train_name,
            "train_type": self.train_type,
            "source_station": self.source_station,
            "destination_station": self.destination_station,
            "distance_km": self.distance_km,
            "seat_capacity": self.seat_capacity,
        }
