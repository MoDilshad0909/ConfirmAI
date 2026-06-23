from . import db
from datetime import datetime

class Station(db.Model):
    __tablename__ = "stations"

    station_code = db.Column(db.String(10), primary_key=True)
    station_name = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=True)
    zone = db.Column(db.String(20), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "station_code": self.station_code,
            "station_name": self.station_name,
            "state": self.state,
            "zone": self.zone
        }
