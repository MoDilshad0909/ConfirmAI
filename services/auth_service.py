import bcrypt
from models import db
from models.user import User
from utils.jwt_utils import generate_token


def register_user(data: dict) -> dict:
    if User.query.filter_by(email=data["email"]).first():
        return None, "Email already registered"

    pw_hash = bcrypt.hashpw(data["password"].encode(), bcrypt.gensalt()).decode()
    user = User(
        email=data["email"],
        password_hash=pw_hash,
        first_name=data["first_name"],
        last_name=data["last_name"],
        role=data.get("role", "passenger"),
    )
    db.session.add(user)
    db.session.commit()
    return user, None


def login_user(email: str, password: str) -> tuple:
    user = User.query.filter_by(email=email).first()
    if not user:
        return None, None, "Invalid email or password"
    if not bcrypt.checkpw(password.encode(), user.password_hash.encode()):
        return None, None, "Invalid email or password"
    token = generate_token(user.user_id, user.role)
    return user, token, None
