import json
from database.db_connection import get_db_connection

def get_subscription_plans(data):
    try:
        board_id = data.get("board_id")
        class_id = data.get("class_id")
        subject_ids = data.get("subject_ids")

        if board_id is None or class_id is None or not subject_ids:
            return {
                "status": "error",
                "code": 400,
                "message": "board_id, class_id, and subject_ids are required",
                "data": []
            }

        conn = get_db_connection()
        if not conn:
            return {
                "status": "error",
                "code": 500,
                "message": "Database connection failed",
                "data": []
            }

        cursor = conn.cursor(dictionary=True)
        subject_ids_json = json.dumps(subject_ids)
        cursor.callproc('sp_get_subscription_plans', (board_id, class_id, subject_ids_json))
        results = []
        for result in cursor.stored_results():
            results = result.fetchall()
            break

        conn.close()
        plans_dict = {}

        for row in results:
            plan_id = row['plan_id']
            if plan_id not in plans_dict:
                plans_dict[plan_id] = {
                    "badge": row['badge'],
                    "base_subject_total": float(row['base_subject_total']),
                    "billing_cycle": row['billing_cycle'],
                    "duration_days": int(row['duration_days']),
                    "features": [],
                    "monthly_divisor": int(row['monthly_divisor']),
                    "plan_discount_percent": float(row['plan_discount_percent']),
                    "plan_id": plan_id,
                    "plan_name": row['plan_name'],
                    "plan_tag": row['plan_tag'],
                    "subject_prices": []
                }
            
            if row.get('feature_name'):
                feature = {
                    "availability": row['availability'],
                    "feature_name": row['feature_name'],
                    "feature_type": row['feature_type']
                }
                if feature not in plans_dict[plan_id]['features']:
                    plans_dict[plan_id]['features'].append(feature)
            
            if row.get('subject_id'):
                subject = {
                    "price": float(row['subject_price']),
                    "subject_id": row['subject_id']
                }
                if subject not in plans_dict[plan_id]['subject_prices']:
                    plans_dict[plan_id]['subject_prices'].append(subject)

        plans_list = list(plans_dict.values())

        return {
            "status": "success",
            "code": 200,
            "message": "Subscription plans loaded successfully",
            "data": plans_list
        }

    except Exception as e:
        return {
            "status": "error",
            "code": 500,
            "message": str(e),
            "data": []
        }

def verify_subscription_amount(data):
    try:
        plan_id = data.get("plan_id")
        board_id = data.get("board_id")
        class_id = data.get("class_id")
        subject_ids = data.get("subject_ids")
        ui_total_amount = data.get("ui_total_amount")
        total_licences = data.get("total_licences")

        if any(v is None for v in [plan_id, board_id, class_id, subject_ids, ui_total_amount, total_licences]):
            return {
                "status": "error",
                "code": 400,
                "message": "All fields (plan_id, board_id, class_id, subject_ids, ui_total_amount, total_licences) are required",
                "data": []
            }

        conn = get_db_connection()
        if not conn:
            return {
                "status": "error",
                "code": 500,
                "message": "Database connection failed",
                "data": []
            }

        cursor = conn.cursor()
        
        subject_ids_json = json.dumps(subject_ids)
        
        result_args = cursor.callproc('sp_verify_subscription_amount', (
            plan_id, 
            board_id, 
            class_id, 
            subject_ids_json, 
            total_licences, 
            0.0
        ))
        
        conn.close()
        
        calculated_amount = float(result_args[5])
        
        if calculated_amount == -1.00:
             return {
                "status": "error",
                "code": 404,
                "message": "Invalid Plan ID or inactive plan",
                "data": []
            }
            
        ui_amount = float(ui_total_amount)
        
        if calculated_amount == ui_amount:
            return {
                "code": 200,
                "data": {
                    "verified_amount": calculated_amount
                },
                "message": "Amount Verified",
                "status": "success"
            }
        else:
             return {
                "status": "error",
                "code": 400,
                "message": f"Amount mismatch. Expected {calculated_amount}, received {ui_amount}",
                "data": []
            }

    except Exception as e:
        return {
            "status": "error",
            "code": 500,
            "message": str(e),
            "data": []
        }

def create_subscription_after_payment(data):
    try:
        plan_id = data.get("plan_id")
        board_id = data.get("board_id")
        class_id = data.get("class_id")
        institute_id = data.get("institute_id")
        subject_ids = data.get("subject_ids", [])
        total_licenses = data.get("total_licenses", 1)
        licences_used = data.get("licences_used", 0)
        transaction_id = data.get("transaction_id")
        subscription_name = data.get("subscription_name")
        ui_total_amount = data.get("ui_total_amount", 0.0)
        coupon_code = data.get("coupon_code")
        
        user_id = data.get("user_id", 1)

        conn = get_db_connection()
        if not conn:
            return {
                "status": "error",
                "code": 500,
                "message": "Database connection failed",
                "data": None
            }

        cursor = conn.cursor()
        
        subject_ids_json = json.dumps(subject_ids)
        
        cursor.callproc('sp_create_subscription', (
            user_id,
            plan_id,
            board_id,
            class_id,
            institute_id,
            subject_ids_json,
            total_licenses,
            licences_used,
            transaction_id,
            subscription_name,
            ui_total_amount,
            coupon_code
        ))
        
        conn.commit()
        conn.close()
        
        return {
            "code": 200,
            "data": None,
            "message": "Subscription added successfully",
            "status": "success"
        }

    except Exception as e:
        return {
            "status": "error",
            "code": 500,
            "message": str(e),
            "data": None
        }
