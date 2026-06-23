from models.train import Train
from models.station import Station
import random
from datetime import datetime, timedelta

class IndianRailAPIClient:
    """
    Wrapper for Indian Railways / IRCTC data.
    Currently acts as an interface to the local seeded database.
    Can be seamlessly swapped out with RapidAPI IRCTC live endpoints in production.
    """
    
    def __init__(self, api_key=None):
        self.api_key = api_key

    def get_live_train_status(self, train_number: str, date: str) -> dict:
        """Fetch live train status (mocked for development)"""
        train = Train.query.filter_by(train_number=train_number).first()
        if not train:
            return {"success": False, "error": "Train not found"}
        
        return {
            "success": True,
            "data": {
                "train_number": train.train_number,
                "train_name": train.train_name,
                "status": random.choice(["ON TIME", "DELAYED", "CANCELLED"]),
                "delay_minutes": random.randint(0, 120) if random.random() > 0.5 else 0,
                "last_updated": datetime.utcnow().isoformat()
            }
        }

    def get_pnr_status(self, pnr: str) -> dict:
        """Fetch live PNR status (mocked for development)"""
        if len(pnr) != 10:
            return {"success": False, "error": "Invalid PNR format"}
            
        status = random.choice(["CNF", "RAC", "WL"])
        return {
            "success": True,
            "data": {
                "pnr": pnr,
                "status": status,
                "current_status": f"{status} {random.randint(1, 100)}" if status != "CNF" else "CNF",
                "booking_status": "WL 120"
            }
        }

    def get_train_schedule(self, train_number: str) -> dict:
        """Fetch timetable for a train (mocked for development)"""
        train = Train.query.filter_by(train_number=train_number).first()
        if not train:
            return {"success": False, "error": "Train not found"}
            
        return {
            "success": True,
            "data": {
                "train_number": train.train_number,
                "train_name": train.train_name,
                "source": train.source_station,
                "destination": train.destination_station,
                "schedule": [
                    {"station": train.source_station, "arrival": "Source", "departure": "10:00"},
                    {"station": "MOCK_INTERMEDIATE", "arrival": "14:00", "departure": "14:15"},
                    {"station": train.destination_station, "arrival": "20:00", "departure": "Destination"}
                ]
            }
        }
