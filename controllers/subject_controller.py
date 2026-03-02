from database.db_connection import get_db_connection


def get_school_class_subjects(data):
    try:
        school_id = data.get("school_id")
        class_id = data.get("class_id")

        if not school_id or not class_id:
            return {
                "status": "error",
                "code": 400,
                "message": "school_id and class_id required",
                "data": []
            }

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT 
                scs.id AS school_class_subject_id,
                s.id AS subject_id,
                s.name AS subject_name
            FROM class_subjects scs
            JOIN subjects s ON scs.subject_id = s.id
            WHERE scs.school_id = %s
            AND scs.class_id = %s
            AND scs.is_active = 1
            ORDER BY s.name ASC
        """, (school_id, class_id))

        subjects = cursor.fetchall()
        conn.close()

        return {
            "status": "success",
            "code": 200,
            "message": "Subjects retrieved successfully",
            "data": subjects
        }

    except Exception as e:
        return {
            "status": "error",
            "code": 500,
            "message": str(e),
            "data": []
        }
      
def save_student_subjects(data):
    try:
        username = data.get("username")
        academic_year = data.get("academic_year")
        class_subject_ids = data.get("class_subject_ids")

        if not username or not academic_year or not class_subject_ids:
            return {
                "status": "error",
                "code": 400,
                "message": "All fields required",
                "data": []
            }

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Get user_id
        cursor.execute(
            "SELECT user_id FROM user_master WHERE username = %s",
            (username,)
        )
        user = cursor.fetchone()

        if not user:
            conn.close()
            return {
                "status": "error",
                "code": 404,
                "message": "User not found",
                "data": []
            }

        user_id = user["user_id"]

        # Get profile
        cursor.execute("""
            SELECT id FROM student_academic_profile
            WHERE user_id = %s AND academic_year = %s
        """, (user_id, academic_year))

        profile = cursor.fetchone()

        if not profile:
            conn.close()
            return {
                "status": "error",
                "code": 404,
                "message": "Academic profile not found",
                "data": []
            }

        profile_id = profile["id"]

        # Delete old selections
        cursor.execute("""
            DELETE FROM student_selected_subjects
            WHERE profile_id = %s
        """, (profile_id,))

        # Insert new
        for cs_id in class_subject_ids:
            cursor.execute("""
                INSERT INTO student_selected_subjects
                (profile_id, class_subject_id)
                VALUES (%s, %s)
            """, (profile_id, cs_id))

        conn.commit()
        conn.close()

        return {
            "status": "success",
            "code": 200,
            "message": "Student subjects saved successfully"
        }

    except Exception as e:
        return {
            "status": "error",
            "code": 500,
            "message": str(e),
            "data": []
        }
    