from models.relationship_model import RelationshipModel

def send_join_request(data):
    try:
        parent_entity_id = data.get("parent_entity_id") # The Teacher, Parent, or Institute
        student_ids = data.get("student_ids") # Expect a list
        
        if not parent_entity_id or not student_ids:
            return {
                "status": "error",
                "code": 400,
                "message": "Both parent_entity_id and student_ids are required",
                "data": []
            }
            
        if not isinstance(student_ids, list):
             return {
                "status": "error",
                "code": 400,
                "message": "student_ids must be an array of target user IDs",
                "data": []
            }
            
        if parent_entity_id in student_ids:
             return {
                "status": "error",
                "code": 400,
                "message": "You cannot send a join request to yourself",
                "data": []
            }

        result = RelationshipModel.send_join_request(parent_entity_id, student_ids)
        
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



