from app import create_app
from flask import json
app = create_app()
with app.app_context():
    from utils.jwt_utils import generate_token
    from models.user import User
    from models import db
    admin_user = User.query.filter_by(role='admin').first()
    if not admin_user:
        admin_user = User(first_name="Admin", last_name="User", email="admin@test.com", password_hash="hash", role="admin")
        db.session.add(admin_user)
        db.session.commit()
    token = generate_token(admin_user.user_id, "admin")

with app.test_client() as client:
    res = client.get('/api/admin/stats', headers={"Authorization": f"Bearer {token}"})
    print("STATUS:", res.status_code)
    print("RESPONSE:", res.get_data(as_text=True))
