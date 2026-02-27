from flask import Flask, request, jsonify
from flask_cors import CORS
from controllers.login_register_controller import (
    suggest_usernames,
    send_register_otp,
    verify_register_otp,
    send_login_otp,
    verify_login
)

app = Flask(__name__)
CORS(app)


@app.route("/suggest-username", methods=["POST"])
def suggest():
    return jsonify(suggest_usernames(request.json))


@app.route("/send-register-otp", methods=["POST"])
def send_reg():
    return jsonify(send_register_otp(request.json))


@app.route("/verify-register-otp", methods=["POST"])
def verify_reg():
    return jsonify(verify_register_otp(request.json))


@app.route("/send-login-otp", methods=["POST"])
def send_login():
    return jsonify(send_login_otp(request.json))


@app.route("/verify-login", methods=["POST"])
def verify_login_route():
    return jsonify(verify_login(request.json))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)