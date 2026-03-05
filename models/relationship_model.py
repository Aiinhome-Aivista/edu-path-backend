from database.db_connection import get_db_connection

class RelationshipModel:
    @staticmethod
    def send_join_request(parent_entity_id, student_ids):
        conn = get_db_connection()
        if not conn:
            raise Exception("Database connection failed")
        
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Fetch the requester's role and name
            cursor.execute(
                "SELECT role, full_name FROM user_master WHERE user_id = %s", (parent_entity_id,)
            )
            requester = cursor.fetchone()
            
            if not requester:
                return {"status": "error", "message": "Requester not found in system."}
                
            req_role = requester['role'].lower()
            req_name = requester['full_name']
            
            # 1. Students cannot send join requests at all
            if req_role == 'student':
                return {"status": "error", "message": "Students are not permitted to send join requests."}
                
            title = "New Join Request"
            message = f"{req_name} has sent you a request to join their network."
            
            success_count = 0
            existing_count = 0
            invalid_role_count = 0
            
            for target_id in student_ids:
                # 2. Fetch the target user's role
                cursor.execute(
                    "SELECT role FROM user_master WHERE user_id = %s", (target_id,)
                )
                target_user = cursor.fetchone()
                
                if not target_user:
                    continue
                    
                target_role = target_user['role'].lower()
                
                # 3. Role Validation Logic
                # If Parent or Teacher -> Can only request Students
                if req_role in ['parent', 'teacher'] and target_role != 'student':
                    invalid_role_count += 1
                    continue
                    
                # If Institute -> Can request Teacher, Parent, or Student
                if req_role == 'institute' and target_role not in ['student', 'teacher', 'parent']:
                    invalid_role_count += 1
                    continue
                
                # 4. Check if relationship already exists
                cursor.execute(
                    "SELECT id, status FROM user_relationships WHERE parent_entity_id = %s AND student_id = %s", 
                    (parent_entity_id, target_id)
                )
                existing = cursor.fetchone()
                
                if existing:
                    if existing['status'] in ['pending', 'accepted']:
                        existing_count += 1
                        continue # Skip this student
                    else:
                        # If rejected previously, we can choose to update it back to pending
                        cursor.execute(
                            "UPDATE user_relationships SET status = 'pending' WHERE id = %s",
                            (existing['id'],)
                        )
                        rel_id = existing['id']
                else:
                    # 2. Insert new relationship
                    cursor.execute(
                        "INSERT INTO user_relationships (parent_entity_id, student_id, status) VALUES (%s, %s, 'pending')",
                        (parent_entity_id, target_id)
                    )
                    rel_id = cursor.lastrowid
                    
                # 3. Create Notification for the target user
                cursor.execute(
                    """INSERT INTO common_notifications 
                       (sender_id, receiver_id, title, message, type, related_entity_id) 
                       VALUES (%s, %s, %s, %s, 'send_join_request', %s)""",
                    (parent_entity_id, target_id, title, message, rel_id)
                )
                
                success_count += 1
                
            conn.commit()
            
            return {
                "status": "success", 
                "message": f"Successfully sent {success_count} request(s). {existing_count} user(s) were already connected. {invalid_role_count} user(s) failed role validation."
            }
            
        finally:
            if conn.is_connected():
                conn.close()


