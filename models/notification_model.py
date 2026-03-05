from database.db_connection import get_db_connection

class NotificationModel:
    @staticmethod
    def get_user_notifications(user_id):
        conn = get_db_connection()
        if not conn:
            raise Exception("Database connection failed")
            
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM common_notifications WHERE receiver_id = %s ORDER BY created_at DESC",
                (user_id,)
            )
            return cursor.fetchall()
        finally:
            if conn.is_connected():
                conn.close()

    @staticmethod
    def respond_to_join_request(relationship_id, student_id, action):
        if action not in ['accepted', 'rejected']:
            raise Exception("Invalid action. Must be 'accepted' or 'rejected'")
            
        conn = get_db_connection()
        if not conn:
            raise Exception("Database connection failed")
            
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Verify relationship belongs to this student and is pending
            cursor.execute(
                "SELECT * FROM user_relationships WHERE id = %s AND student_id = %s AND status = 'pending'",
                (relationship_id, student_id)
            )
            rel = cursor.fetchone()
            
            if not rel:
                return {"status": "error", "message": "Join request not found or already processed."}
                
            # Update relationship status
            cursor.execute(
                "UPDATE user_relationships SET status = %s WHERE id = %s",
                (action, relationship_id)
            )
            
            # Mark the associated notification as read
            cursor.execute(
                "UPDATE common_notifications SET is_read = 1 WHERE relationship_id = %s AND type = 'send_join_request'",
                (relationship_id,)
            )
            
            # (Optional) Notify the requester that the student accepted/rejected
            cursor.execute(
                "SELECT full_name FROM user_master WHERE user_id = %s", (student_id,)
            )
            student = cursor.fetchone()
            student_name = student['full_name'] if student else "A student"
            
            notify_title = f"Request {action.capitalize()}"
            notify_message = f"{student_name} has {action} your join request."
            
            cursor.execute(
                """INSERT INTO common_notifications 
                   (sender_id, receiver_id, title, message, type, relationship_id) 
                   VALUES (%s, %s, %s, %s, 'system_alert', %s)""",
                (student_id, rel['parent_entity_id'], notify_title, notify_message, relationship_id)
            )
            
            conn.commit()
            return {"status": "success", "message": f"Join request {action} successfully"}
            
        finally:
            if conn.is_connected():
                conn.close()
