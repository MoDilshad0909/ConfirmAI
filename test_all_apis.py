from app import create_app
from flask import json
app = create_app()
with app.app_context():
    from utils.jwt_utils import generate_token
    from models.user import User
    admin_user = User.query.filter_by(role='admin').first()
    token = generate_token(admin_user.user_id, "admin")

with app.test_client() as client:
    headers = {"Authorization": f"Bearer {token}"}
    for ep in ["stats", "users", "predictions", "searches", "analytics", "traffic", "model", "logs"]:
        res = client.get(f'/api/admin/{ep}', headers=headers)
        if res.status_code != 200:
            print(f"FAILED {ep}: {res.status_code} - {res.get_data(as_text=True)}")
        else:
            print(f"OK {ep}")
