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
