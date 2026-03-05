import json
from models.subscription_model import SubscriptionModel

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

        subject_ids_json = json.dumps(subject_ids)
        
        # Abstraction: Call to Model layer handles all Database Logic
        results = SubscriptionModel.get_subscription_plans(board_id, class_id, subject_ids_json)

        # Presentation formatting
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
        user_id = data.get("user_id")
        plan_id = data.get("plan_id")
        board_id = data.get("board_id")
        class_id = data.get("class_id")
        subject_ids = data.get("subject_ids")
        ui_total_amount = data.get("ui_total_amount")
        total_licences = data.get("total_licences")

        if any(v is None for v in [user_id, plan_id, board_id, class_id, subject_ids, ui_total_amount, total_licences]):
            return {
                "status": "error",
                "code": 400,
                "message": "All fields (user_id, plan_id, board_id, class_id, subject_ids, ui_total_amount, total_licences) are required",
                "data": []
            }

        subject_ids_json = json.dumps(subject_ids)
        
        # Abstraction: Model processes OUT parameter fetching silently
        calculated_amount = SubscriptionModel.verify_subscription_amount(
            user_id, plan_id, board_id, class_id, subject_ids_json, total_licences
        )
        
        if calculated_amount == -2.00:
             return {
                "status": "error",
                "code": 403,
                "message": "Students are restricted to a maximum of 1 license.",
                "data": []
            }
            
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
        user_id = data.get("user_id")
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
        
        if user_id is None:
            return {
                "status": "error",
                "code": 400,
                "message": "user_id is required",
                "data": None
            }
        subject_ids_json = json.dumps(subject_ids)
        
        # Abstraction: Transaction handling via SubscriptionModel
        SubscriptionModel.create_subscription(
            user_id, plan_id, board_id, class_id, institute_id, subject_ids_json, 
            total_licenses, licences_used, transaction_id, subscription_name, 
            ui_total_amount, coupon_code
        )
        
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
