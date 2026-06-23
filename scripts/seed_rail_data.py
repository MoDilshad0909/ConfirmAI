import os
import sys
import random

# Add parent directory to path so we can import app modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from models import db
from models.station import Station
from models.train import Train

app = create_app()

stations_data = [
    {"code": "NDLS", "name": "New Delhi", "state": "Delhi", "zone": "NR"},
    {"code": "CSMT", "name": "Chhatrapati Shivaji Maharaj Terminus", "state": "Maharashtra", "zone": "CR"},
    {"code": "HWH", "name": "Howrah Junction", "state": "West Bengal", "zone": "ER"},
    {"code": "MAS", "name": "Chennai Central", "state": "Tamil Nadu", "zone": "SR"},
    {"code": "SBC", "name": "KSR Bengaluru City", "state": "Karnataka", "zone": "SWR"},
    {"code": "BDTS", "name": "Bandra Terminus", "state": "Maharashtra", "zone": "WR"},
    {"code": "PNBE", "name": "Patna Junction", "state": "Bihar", "zone": "ECR"},
    {"code": "LKO", "name": "Lucknow Charbagh", "state": "Uttar Pradesh", "zone": "NR"},
    {"code": "AII", "name": "Ajmer Junction", "state": "Rajasthan", "zone": "NWR"},
    {"code": "GKP", "name": "Gorakhpur Junction", "state": "Uttar Pradesh", "zone": "NER"},
    {"code": "CNB", "name": "Kanpur Central", "state": "Uttar Pradesh", "zone": "NCR"},
    {"code": "BCT", "name": "Mumbai Central", "state": "Maharashtra", "zone": "WR"},
    {"code": "SDAH", "name": "Sealdah", "state": "West Bengal", "zone": "ER"},
    {"code": "BZA", "name": "Vijayawada Junction", "state": "Andhra Pradesh", "zone": "SCR"},
    {"code": "SC", "name": "Secunderabad Junction", "state": "Telangana", "zone": "SCR"},
    {"code": "ADI", "name": "Ahmedabad Junction", "state": "Gujarat", "zone": "WR"},
    {"code": "PUNE", "name": "Pune Junction", "state": "Maharashtra", "zone": "CR"},
    {"code": "JP", "name": "Jaipur", "state": "Rajasthan", "zone": "NWR"},
    {"code": "BPL", "name": "Bhopal Junction", "state": "Madhya Pradesh", "zone": "WCR"},
    {"code": "BSB", "name": "Varanasi Junction", "state": "Uttar Pradesh", "zone": "NR"},
    {"code": "ASR", "name": "Amritsar Junction", "state": "Punjab", "zone": "NR"},
    {"code": "CBE", "name": "Coimbatore Junction", "state": "Tamil Nadu", "zone": "SR"},
    {"code": "TBM", "name": "Tambaram", "state": "Tamil Nadu", "zone": "SR"},
    {"code": "KYN", "name": "Kalyan Junction", "state": "Maharashtra", "zone": "CR"},
    {"code": "KCG", "name": "Kacheguda", "state": "Telangana", "zone": "SCR"},
    {"code": "MYS", "name": "Mysuru Junction", "state": "Karnataka", "zone": "SWR"},
    {"code": "YPR", "name": "Yesvantpur Junction", "state": "Karnataka", "zone": "SWR"},
    {"code": "PRYJ", "name": "Prayagraj Junction", "state": "Uttar Pradesh", "zone": "NCR"},
    {"code": "DDN", "name": "Dehradun", "state": "Uttarakhand", "zone": "NR"},
    {"code": "CDG", "name": "Chandigarh", "state": "Chandigarh", "zone": "NR"},
]

trains_data = [
    # Rajdhani Express
    {"number": "12951", "name": "MUMBAI RAJDHANI", "type": "RAJ", "src": "BCT", "dest": "NDLS", "seats": 850},
    {"number": "12952", "name": "NDLS BCT RAJDHANI", "type": "RAJ", "src": "NDLS", "dest": "BCT", "seats": 850},
    {"number": "12301", "name": "HOWRAH RAJDHANI", "type": "RAJ", "src": "HWH", "dest": "NDLS", "seats": 900},
    {"number": "12302", "name": "HOWRAH RAJDHANI", "type": "RAJ", "src": "NDLS", "dest": "HWH", "seats": 900},
    {"number": "22691", "name": "RAJDHANI EXP", "type": "RAJ", "src": "SBC", "dest": "NDLS", "seats": 800},
    {"number": "22692", "name": "SBC RAJDHANI", "type": "RAJ", "src": "NDLS", "dest": "SBC", "seats": 800},

    # Shatabdi Express
    {"number": "12001", "name": "NDLS SHT", "type": "SHT", "src": "BPL", "dest": "NDLS", "seats": 600},
    {"number": "12002", "name": "BPL SHT", "type": "SHT", "src": "NDLS", "dest": "BPL", "seats": 600},
    {"number": "12005", "name": "KALKA SHTBDI", "type": "SHT", "src": "NDLS", "dest": "KLK", "seats": 550},
    {"number": "12009", "name": "SHATABDI EXP", "type": "SHT", "src": "BCT", "dest": "ADI", "seats": 500},

    # Superfast Express
    {"number": "12615", "name": "GRAND TRUNK EXP", "type": "SF", "src": "MAS", "dest": "NDLS", "seats": 1200},
    {"number": "12616", "name": "GRAND TRUNK EXP", "type": "SF", "src": "NDLS", "dest": "MAS", "seats": 1200},
    {"number": "12839", "name": "CHENNAI MAIL", "type": "SF", "src": "HWH", "dest": "MAS", "seats": 1400},
    {"number": "12840", "name": "HOWRAH MAIL", "type": "SF", "src": "MAS", "dest": "HWH", "seats": 1400},
    {"number": "12723", "name": "TELANGANA EXP", "type": "SF", "src": "HYB", "dest": "NDLS", "seats": 1250},
    {"number": "12724", "name": "TELANGANA EXP", "type": "SF", "src": "NDLS", "dest": "HYB", "seats": 1250},
    
    # Duronto Express
    {"number": "12261", "name": "CSMT HWH DURONTO", "type": "DUR", "src": "CSMT", "dest": "HWH", "seats": 800},
    {"number": "12262", "name": "HWH CSMT DURONTO", "type": "DUR", "src": "HWH", "dest": "CSMT", "seats": 800},
    {"number": "12267", "name": "RJT DEE DURONTO", "type": "DUR", "src": "RJT", "dest": "DEE", "seats": 700},
    {"number": "12268", "name": "DEE RJT DURONTO", "type": "DUR", "src": "DEE", "dest": "RJT", "seats": 700},

    # Express / Mail
    {"number": "11019", "name": "KONARK EXPRESS", "type": "EXP", "src": "CSMT", "dest": "BBS", "seats": 1100},
    {"number": "11020", "name": "KONARK EXPRESS", "type": "EXP", "src": "BBS", "dest": "CSMT", "seats": 1100},
    {"number": "13005", "name": "AMRITSAR MAIL", "type": "EXP", "src": "HWH", "dest": "ASR", "seats": 1500},
    {"number": "13006", "name": "HOWRAH MAIL", "type": "EXP", "src": "ASR", "dest": "HWH", "seats": 1500},
]

def seed_db():
    with app.app_context():
        # Ensure tables exist
        db.create_all()
        
        # Clean existing mock data from these tables safely
        print("Cleaning old station and train data...")
        Station.query.delete()
        Train.query.delete()

        # Seed Stations
        print("Seeding Station Master Dataset...")
        for st in stations_data:
            s = Station(
                station_code=st["code"],
                station_name=st["name"],
                state=st["state"],
                zone=st["zone"]
            )
            db.session.add(s)

        # Seed Trains
        print("Seeding IRCTC-style Train Data...")
        for tr in trains_data:
            t = Train(
                train_number=tr["number"],
                train_name=tr["name"],
                train_type=tr["type"],
                source_station=tr["src"],
                destination_station=tr["dest"],
                seat_capacity=tr["seats"],
                distance_km=random.randint(400, 2500)
            )
            db.session.add(t)

        db.session.commit()
        print(f"Successfully seeded {len(stations_data)} stations and {len(trains_data)} trains!")

if __name__ == "__main__":
    seed_db()
