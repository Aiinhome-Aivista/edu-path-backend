import random
import string
import smtplib
import os
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from database.db_connection import get_db_connection


REGISTER_OTP_STORE = {}
LOGIN_OTP_STORE = {}


# ======================================
# UTILITIES
# ======================================

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))


def send_email(email, otp, purpose):
    try:
        smtp_server = os.getenv("MAIL_SERVER")
        smtp_port = int(os.getenv("MAIL_PORT"))
        smtp_user = os.getenv("MAIL_USERNAME")
        smtp_pass = os.getenv("MAIL_PASSWORD")

        subject = "EDU-PATH Email Verification OTP"
        body = f"""
Hello,

Your OTP for registration is: {otp}
This OTP is valid for 5 minutes.

Regards,
EDU-PATH Team
"""
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = smtp_user
        msg["To"] = email

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, email, msg.as_string())
        server.quit()

        return True
    except Exception as e:
        print("SMTP ERROR:", e)
        return False


# ======================================
# USERNAME SUGGESTION
# ======================================

def suggest_usernames(data):
    base = data.get("username")

    if not base:
        return {"status": "error", "message": "Username required"}

    conn = get_db_connection()
    cursor = conn.cursor()

    suggestions = []
    counter = 0

    while len(suggestions) < 5:
        if counter == 0:
            uname = base
        else:
            uname = f"{base}{random.randint(100,999)}"

        cursor.execute("SELECT user_id FROM user_master WHERE username=%s", (uname,))
        if not cursor.fetchone():
            suggestions.append(uname)

        counter += 1

    conn.close()

    return {"status": "success", "suggestions": suggestions}


# ======================================
# REGISTER - SEND OTP
# ======================================

def send_register_otp(data):
    email = data.get("email")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT user_id FROM user_master WHERE email=%s", (email,))
    if cursor.fetchone():
        conn.close()
        return {"status": "error", "message": "Email already registered"}

    conn.close()

    otp = generate_otp()

    REGISTER_OTP_STORE[email] = {
        "otp": otp,
        "expiry": datetime.now() + timedelta(minutes=5),
        "data": data
    }

    send_email(email, otp, "Registration")

    return {"status": "success", "message": "OTP sent for registration"}


# ======================================
# VERIFY REGISTER OTP
# ======================================

def verify_register_otp(data):
    email = data.get("email")
    otp = data.get("otp")

    if email not in REGISTER_OTP_STORE:
        return {"status": "error", "message": "No OTP request found"}

    record = REGISTER_OTP_STORE[email]

    if datetime.now() > record["expiry"]:
        del REGISTER_OTP_STORE[email]
        return {"status": "error", "message": "OTP expired"}

    if record["otp"] != otp:
        return {"status": "error", "message": "Invalid OTP"}

    user_data = record["data"]

    conn = get_db_connection()
    cursor = conn.cursor()

    hashed = generate_password_hash(user_data["password"])

    cursor.execute("""
        INSERT INTO user_master
        (role, full_name, username, email, mobile,
         password, is_active, is_verified,
         created_at, updated_at)
        VALUES (%s,%s,%s,%s,%s,%s,1,1,NOW(),NOW())
    """, (
        user_data["role"],
        user_data["full_name"],
        user_data["username"],
        user_data["email"],
        user_data["mobile"],
        hashed
    ))

    conn.commit()
    conn.close()

    del REGISTER_OTP_STORE[email]

    return {"status": "success", "message": "Registration successful"}


# ======================================
# LOGIN - SEND OTP
# ======================================

def send_login_otp(data):
    username = data.get("username")
    email = data.get("email")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM user_master WHERE username=%s AND email=%s",
        (username, email)
    )

    user = cursor.fetchone()
    conn.close()

    if not user:
        return {"status": "error", "message": "Invalid username or email"}

    otp = generate_otp()

    LOGIN_OTP_STORE[username] = {
        "otp": otp,
        "expiry": datetime.now() + timedelta(minutes=5)
    }

    send_email(email, otp, "Login")

    return {"status": "success", "message": "OTP sent for login"}


# ======================================
# VERIFY LOGIN
# ======================================

def verify_login(data):
    username = data.get("username")
    otp = data.get("otp")
    password = data.get("password")

    if username not in LOGIN_OTP_STORE:
        return {"status": "error", "message": "No login OTP found"}

    record = LOGIN_OTP_STORE[username]

    if datetime.now() > record["expiry"]:
        del LOGIN_OTP_STORE[username]
        return {"status": "error", "message": "OTP expired"}

    if record["otp"] != otp:
        return {"status": "error", "message": "Invalid OTP"}

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM user_master WHERE username=%s", (username,))
    user = cursor.fetchone()
    conn.close()

    if not check_password_hash(user["password"], password):
        return {"status": "error", "message": "Invalid password"}

    del LOGIN_OTP_STORE[username]

    return {
        "status": "success",
        "message": "Login successful",
        "user": {
            "user_id": user["user_id"],
            "username": user["username"],
            "role": user["role"]
        }
    }