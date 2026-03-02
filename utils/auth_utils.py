import jwt
import datetime
import os

SECRET_KEY = os.getenv("JWT_SECRET_KEY")

def generate_token(user_data):
    payload = {
        "user_id": user_data["user_id"],
        "username": user_data["username"],
        "role": user_data["role"],
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def decode_token(token):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None