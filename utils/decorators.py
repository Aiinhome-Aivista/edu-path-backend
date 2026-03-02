from functools import wraps
from flask import request, jsonify
from utils.auth_utils import decode_token

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            return jsonify({"message": "Token is missing"}), 401
        
        # Expecting "Bearer <token>"
        token = token.split(" ")[1] if " " in token else token
        data = decode_token(token)
        
        if not data:
            return jsonify({"message": "Token is invalid or expired"}), 401
        
        return f(data, *args, **kwargs)
    return decorated