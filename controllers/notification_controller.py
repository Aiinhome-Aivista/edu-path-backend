from models.notification_model import NotificationModel

def get_notifications(user_id):
    try:
        if not user_id:
             return {
                "status": "error",
                "code": 400,
                "message": "user_id is required",
                "data": []
            }
            
        notifications = NotificationModel.get_user_notifications(user_id)
        
        return {
            "status": "success",
            "code": 200,
            "message": "Notifications fetched successfully",
            "data": notifications
        }
        
    except Exception as e:
        return {
            "status": "error",
            "code": 500,
            "message": str(e),
            "data": []
        }

def respond_join_request(data):
    try:
        student_id = data.get("student_id")
        relationship_id = data.get("relationship_id")
        action = data.get("action") # 'accepted' or 'rejected'
        
        if not student_id or not relationship_id or not action:
            return {
                "status": "error",
                "code": 400,
                "message": "student_id, relationship_id, and action are required",
                "data": []
            }

        result = NotificationModel.respond_to_join_request(relationship_id, student_id, action)
        
        if result['status'] == 'error':
             return {
                "status": "error",
                "code": 400,
                "message": result['message'],
                "data": []
            }
            
        return {
            "status": "success",
            "code": 200,
            "message": result['message'],
            "data": []
        }

    except Exception as e:
        return {
            "status": "error",
            "code": 500,
            "message": str(e),
            "data": []
        }
