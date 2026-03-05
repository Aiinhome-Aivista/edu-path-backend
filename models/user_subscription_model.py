from database.db_connection import get_db_connection

class UserSubscriptionModel:
    @staticmethod
    def get_user_subscriptions(user_id):
        conn = get_db_connection()
        if not conn:
            raise Exception("Database connection failed")
            
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT 
                    us.*,
                    sp.name AS plan_name
                FROM user_subscriptions us
                LEFT JOIN subscription_plans sp ON us.plan_id = sp.id
                WHERE us.user_id = %s
                ORDER BY us.id DESC
            """
            cursor.execute(query, (user_id,))
            return cursor.fetchall()
        finally:
            if conn.is_connected():
                conn.close()

    @staticmethod
    def assign_subscription_license(parent_entity_id, student_id, user_subscription_id):
        conn = get_db_connection()
        if not conn:
            raise Exception("Database connection failed")
            
        try:
            cursor = conn.cursor(dictionary=True)
            
            # 1. Verify Parent owns the subscription AND has available licenses
            cursor.execute(
                """SELECT obj.*, p.duration_days, p.name AS plan_name 
                   FROM user_subscriptions obj
                   JOIN subscription_plans p ON obj.plan_id = p.id
                   WHERE obj.id = %s AND obj.user_id = %s FOR UPDATE""",
                (user_subscription_id, parent_entity_id)
            )
            sub = cursor.fetchone()
            if not sub:
                return {"status": "error", "message": "Subscription not found or ownership invalid."}
                
            if sub['licences_used'] >= sub['total_licenses']:
                return {"status": "error", "message": "No available licenses remaining."}
                
            # 2. Verify Relationship is Accepted
            cursor.execute(
                "SELECT status FROM user_relationships WHERE parent_entity_id = %s AND student_id = %s",
                (parent_entity_id, student_id)
            )
            rel = cursor.fetchone()
            if not rel or rel['status'] != 'accepted':
                 return {"status": "error", "message": "Student is not connected. Connect first before assigning licenses."}
                 
            # 3. Prevent Duplicates
            cursor.execute(
                "SELECT id FROM assigned_subscription_licenses WHERE user_subscription_id = %s AND student_id = %s",
                (user_subscription_id, student_id)
            )
            if cursor.fetchone():
                return {"status": "error", "message": "This student already has a license for this subscription."}
                
            # 4. Perform the Assignment
            from datetime import date, timedelta
            start_date = date.today()
            end_date = start_date + timedelta(days=sub['duration_days'])
            
            cursor.execute(
                """INSERT INTO assigned_subscription_licenses 
                   (user_subscription_id, parent_entity_id, student_id, start_date, end_date) 
                   VALUES (%s, %s, %s, %s, %s)""",
                (user_subscription_id, parent_entity_id, student_id, start_date, end_date)
            )
            
            # 5. Increment License Usage
            cursor.execute(
                "UPDATE user_subscriptions SET licences_used = licences_used + 1 WHERE id = %s",
                (user_subscription_id,)
            )
            
            # 6. Notify the Student
            cursor.execute("SELECT full_name FROM user_master WHERE user_id = %s", (parent_entity_id,))
            parent = cursor.fetchone()
            parent_name = parent['full_name'] if parent else "Someone"
            
            notify_title = "New Course License Assigned"
            notify_msg = f"{parent_name} matched you to a new '{sub['plan_name']}' plan. Open your Dashboard to start learning!"
            
            cursor.execute(
                """INSERT INTO common_notifications 
                   (sender_id, receiver_id, title, message, type, related_entity_id) 
                   VALUES (%s, %s, %s, %s, 'system_alert', %s)""",
                (parent_entity_id, student_id, notify_title, notify_msg, user_subscription_id)
            )
            
            conn.commit()
            return {"status": "success", "message": "License assigned successfully!"}
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            if conn.is_connected():
                conn.close()
