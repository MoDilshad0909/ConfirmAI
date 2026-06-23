from app import create_app
from models import db
from models.user import User
from models.prediction import Prediction, SearchHistory

app = create_app()
with app.app_context():
    print(f"Total Users: {User.query.count()}")
    print(f"Total Predictions: {Prediction.query.count()}")
    print(f"Total Searches: {SearchHistory.query.count()}")
