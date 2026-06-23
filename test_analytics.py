from app import create_app
from models import db
from models.analytics import UserActivityLog, LoginLog, PredictionLog, AdminLog, WebsiteAnalytics

app = create_app()
with app.app_context():
    db.create_all()
    print("Analytics tables created successfully.")
