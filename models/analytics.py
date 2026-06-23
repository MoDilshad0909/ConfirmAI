from models import db
from datetime import datetime

class UserActivityLog(db.Model):
    __tablename__ = "user_activity_logs"
    log_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    action = db.Column(db.String(255), nullable=False)
    ip_address = db.Column(db.String(50), nullable=True)
    browser = db.Column(db.String(255), nullable=True)
    device = db.Column(db.String(255), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

class LoginLog(db.Model):
    __tablename__ = "login_logs"
    log_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    login_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    logout_time = db.Column(db.DateTime, nullable=True)
    ip_address = db.Column(db.String(50), nullable=True)
    browser = db.Column(db.String(255), nullable=True)
    device = db.Column(db.String(255), nullable=True)

class PredictionLog(db.Model):
    __tablename__ = "prediction_logs"
    log_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    prediction_id = db.Column(db.Integer, db.ForeignKey("predictions.prediction_id", ondelete="CASCADE"), nullable=True)
    train_number = db.Column(db.String(10), nullable=False)
    route = db.Column(db.String(20), nullable=True)
    predicted_status = db.Column(db.String(10), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

class AdminLog(db.Model):
    __tablename__ = "admin_logs"
    log_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    admin_id = db.Column(db.Integer, db.ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    action = db.Column(db.String(255), nullable=False)
    target_id = db.Column(db.String(50), nullable=True)
    ip_address = db.Column(db.String(50), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

class WebsiteAnalytics(db.Model):
    __tablename__ = "website_analytics"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    visitor_id = db.Column(db.String(100), nullable=True, index=True)
    is_logged_in = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, nullable=True)
    device_type = db.Column(db.String(50), nullable=True)
    browser = db.Column(db.String(100), nullable=True)
    country = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(100), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    endpoint = db.Column(db.String(255), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
