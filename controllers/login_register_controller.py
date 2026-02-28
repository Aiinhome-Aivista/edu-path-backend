import random
import string
import smtplib
import os
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from database.db_connection import get_db_connection
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


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

        # ============================
        # Dynamic Subject
        # ============================
        subject = f"EDU-PATH | {purpose} OTP Verification"

        # ============================
        # Dynamic Text Version
        # ============================
        text_body = f"""
Hello,

Your OTP for {purpose.lower()} is: {otp}

This OTP is valid for 5 minutes.

If you did not request this, please ignore this email.

Regards,
EDU-PATH Team
"""

        # ============================
        # HTML Version (Professional Look)
        # ============================
        html_body = f"""
<html>
  <body style="font-family: Arial, sans-serif; background-color:#f4f6f9; padding:20px;">
    <div style="max-width:500px; margin:auto; background:white; padding:25px; border-radius:8px;">
      
      <h2 style="color:#2c3e50;">EDU-PATH</h2>
      <p>Hello,</p>

      <p>You requested an OTP for <b>{purpose}</b>.</p>

      <div style="text-align:center; margin:20px 0;">
        <span style="font-size:28px; letter-spacing:4px; font-weight:bold; color:#34495e;">
          {otp}
        </span>
      </div>

      <p>This OTP is valid for <b>5 minutes</b>.</p>

      <p style="color:#7f8c8d; font-size:13px;">
        If you did not request this, please ignore this email.
      </p>

      <hr style="margin:20px 0;">
      <p style="font-size:12px; color:#95a5a6;">
        © {datetime.now().year} EDU-PATH. All rights reserved.
      </p>

    </div>
  </body>
</html>
"""

        # ============================
        # Build Email
        # ============================
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = smtp_user
        message["To"] = email

        message.attach(MIMEText(text_body, "plain"))
        message.attach(MIMEText(html_body, "html"))

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, email, message.as_string())
        server.quit()

        return True

    except Exception as e:
        print("SMTP ERROR:", e)
        return False

# ======================================
# USERNAME SUGGESTION (STRICT UNIQUE)
# ======================================

def suggest_usernames(data):
    base = data.get("username")

    if not base:
        return {"status": "error", "message": "Username required"}

    conn = get_db_connection()
    cursor = conn.cursor()

    suggestions = set()

    while len(suggestions) < 5:
        uname = f"{base}{random.randint(100,999)}"

        cursor.execute(
            "SELECT user_id FROM user_master WHERE username=%s",
            (uname,)
        )

        if not cursor.fetchone():
            suggestions.add(uname)

    conn.close()

    return {
        "status": "success",
        "suggestions": list(suggestions)
    }


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
# VERIFY REGISTER OTP (INSERT USER)
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

    # Double check username uniqueness
    cursor.execute(
        "SELECT user_id FROM user_master WHERE username=%s",
        (user_data["username"],)
    )

    if cursor.fetchone():
        conn.close()
        return {"status": "error", "message": "Username already exists"}

    cursor.execute("""
        INSERT INTO user_master
        (role, full_name, username, email, mobile,
         is_active, is_verified,
         created_at, updated_at)
        VALUES (%s,%s,%s,%s,%s,1,1,NOW(),NOW())
    """, (
        user_data["role"],
        user_data["full_name"],
        user_data["username"],
        user_data["email"],
        user_data["mobile"]
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
# VERIFY LOGIN (OTP ONLY)
# ======================================

def verify_login(data):
    username = data.get("username")
    otp = data.get("otp")

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

    cursor.execute(
        "SELECT user_id, username, role FROM user_master WHERE username=%s",
        (username,)
    )

    user = cursor.fetchone()
    conn.close()

    del LOGIN_OTP_STORE[username]

    return {
        "status": "success",
        "message": "Login successful",
        "user": user
    }