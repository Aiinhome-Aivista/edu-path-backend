from flask import Flask, request, jsonify
from flask_cors import CORS
from controllers.academic_year_controller import get_academic_year
from controllers.board_controller import get_boards
from controllers.class_controller import get_classes_by_school
from controllers.login_register_controller import (
    suggest_usernames,
    send_register_otp,
    verify_register_otp,
    send_login_otp,
    verify_login
)
from controllers.school_controller import get_schools_by_board
from controllers.student_assign_test import create_student_test
from controllers.student_profile_controller import get_student_full_profile_secure, save_student_academic_profile
from controllers.study_plan_controller import get_study_plan_dashboard
from utils.decorators import token_required
from controllers.subject_controller import get_school_class_subjects, save_student_subjects
from controllers.subscription_controller import get_subscription_plans, verify_subscription_amount, create_subscription_after_payment

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

@app.route("/boards", methods=["GET"])
def boards():
    return jsonify(get_boards())

@app.route("/schools", methods=["POST"])
def schools():
    return jsonify(get_schools_by_board(request.json))

@app.route("/classes", methods=["POST"])
def classes():
    return jsonify(get_classes_by_school(request.json))

@app.route("/academic-year", methods=["POST"])
def academic_year():
    return jsonify(get_academic_year(request.json))

@app.route("/save-student-academic-profile", methods=["POST"])
@token_required
def save_student_profile(current_user):
    data = request.json
    return jsonify(save_student_academic_profile(data))

@app.route("/class-subjects", methods=["POST"])
def class_subjects():
    return jsonify(get_school_class_subjects(request.json))

@app.route("/save-student-subjects", methods=["POST"])
def save_subjects():
    return jsonify(save_student_subjects(request.json))

@app.route("/student-dashboard", methods=["POST"])
@token_required
def student_dashboard(current_user): 
    return jsonify(get_student_full_profile_secure(current_user))

@app.route("/study-plan", methods=["GET"])
@token_required
def study_plan_dashboard(current_user):
    return jsonify(get_study_plan_dashboard(current_user))

@app.route("/plans", methods=["POST"])
def subscription_plans():
    return jsonify(get_subscription_plans(request.json))

@app.route("/create-student-test", methods=["POST"])
def create_student_test_controller():
	return create_student_test()

@app.route("/validate-plan-amount", methods=["POST"])
def verify_payment_amount():
    return jsonify(verify_subscription_amount(request.json))

@app.route("/complete-subscription", methods=["POST"])
def complete_subscription():
    return jsonify(create_subscription_after_payment(request.json))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)