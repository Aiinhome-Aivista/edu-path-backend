from database.db_connection import get_db_connection

class SubscriptionModel:
    @staticmethod
    def get_subscription_plans(board_id, class_id, subject_ids_json):
        conn = get_db_connection()
        if not conn:
            raise Exception("Database connection failed")
        
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.callproc('sp_get_subscription_plans', (board_id, class_id, subject_ids_json))
            results = []
            for result in cursor.stored_results():
                results = result.fetchall()
                break # We only expect one result set from this SP
            return results
        finally:
            if conn.is_connected():
                conn.close()

    @staticmethod
    def verify_subscription_amount(user_id, plan_id, board_id, class_id, subject_ids_json, total_licences):
        conn = get_db_connection()
        if not conn:
            raise Exception("Database connection failed")
            
        try:
            cursor = conn.cursor()
            # In mysql-connector-python, OUT parameters are returned inside 
            # a modified copy of the input sequence via callproc()
            result_args = cursor.callproc('sp_verify_subscription_amount', (
                user_id,
                plan_id, 
                board_id, 
                class_id, 
                subject_ids_json, 
                total_licences, 
                0.0 # Placeholder for the OUT p_calculated_amount parameter
            ))
            
            # The OUT parameter is the 7th argument (index 6)
            calculated_amount = float(result_args[6])
            return calculated_amount
        finally:
            if conn.is_connected():
                conn.close()

    @staticmethod
    def create_subscription(user_id, plan_id, board_id, class_id, institute_id, subject_ids_json, total_licenses, licences_used, transaction_id, subscription_name, amount_paid, coupon_code):
        conn = get_db_connection()
        if not conn:
            raise Exception("Database connection failed")
            
        try:
            cursor = conn.cursor()
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
                amount_paid,
                coupon_code
            ))
            conn.commit()
        finally:
            if conn.is_connected():
                conn.close()

