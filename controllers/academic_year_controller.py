from datetime import datetime


def get_academic_year(data):
    try:
        board_id = data.get("board_id")
        class_id = data.get("class_id")

        if not board_id or not class_id:
            return {
                "status": "error",
                "code": 400,
                "message": "board_id and class_id required",
                "data": []
            }

        current_year = datetime.now().year
        next_year = current_year + 1

        academic_year = f"{current_year}-{next_year}"

        return {
            "status": "success",
            "code": 200,
            "message": "Academic Years fetched successfully",
            "data": [
                {
                    "year": academic_year
                }
            ]
        }

    except Exception as e:
        return {
            "status": "error",
            "code": 500,
            "message": str(e),
            "data": []
        }