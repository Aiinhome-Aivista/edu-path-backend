from database.db_connection import get_db_connection


def get_classes_by_school(data):
    try:
        school_id = data.get("school_id")

        if not school_id:
            return {
                "status": "error",
                "code": 400,
                "message": "school_id required",
                "data": []
            }

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT c.id, c.name
            FROM school_classes sc
            JOIN classes c ON sc.class_id = c.id
            WHERE sc.school_id = %s
            ORDER BY c.id ASC
        """, (school_id,))

        classes = cursor.fetchall()
        conn.close()

        return {
            "status": "success",
            "code": 200,
            "message": "Classes fetched successfully",
            "data": classes
        }

    except Exception as e:
        return {
            "status": "error",
            "code": 500,
            "message": str(e),
            "data": []
        }