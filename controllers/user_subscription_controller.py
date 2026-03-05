from models.user_subscription_model import UserSubscriptionModel

def get_user_subscriptions(data):
    try:
        user_id = data.get("user_id")
        
        if not user_id:
            return {
                "status": "error",
                "code": 400,
                "message": "user_id is required",
                "data": []
            }

        subscriptions = UserSubscriptionModel.get_user_subscriptions(user_id)
        
        # Format the datetime objects nicely for JSON serialization if needed
        for sub in subscriptions:
            for key, value in sub.items():
                if hasattr(value, 'isoformat'):
                    sub[key] = value.isoformat()

        return {
            "status": "success",
            "code": 200,
            "message": "User subscriptions fetched successfully",
            "data": subscriptions
        }

    except Exception as e:
        return {
            "status": "error",
            "code": 500,
            "message": str(e),
            "data": []
        }

def assign_subscription_license(data):
    try:
        parent_entity_id = data.get("parent_entity_id")
        student_id = data.get("student_id")
        user_subscription_id = data.get("user_subscription_id")
        
        if any(v is None for v in [parent_entity_id, student_id, user_subscription_id]):
            return {
                "status": "error",
                "code": 400,
                "message": "parent_entity_id, student_id, and user_subscription_id are required",
                "data": None
            }
            
        result = UserSubscriptionModel.assign_subscription_license(parent_entity_id, student_id, user_subscription_id)
        
        if result.get("status") == "error":
             return {
                "status": "error", 
                "code": 400, 
                "message": result["message"], 
                "data": None
            }
            
        return {
            "code": 200,
            "data": None,
            "message": result["message"],
            "status": "success"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "code": 500,
            "message": str(e),
            "data": None
        }
