import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import db
from models.analytics import UserActivityLog, LoginLog, PredictionLog, AdminLog, WebsiteAnalytics

with app.app_context():
    db.create_all()
    print("Analytics tables created successfully.")
