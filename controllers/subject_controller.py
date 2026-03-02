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
                "message": "username, academic_year and class_subject_ids required",
                "data": []
            }

        if not isinstance(class_subject_ids, list):
            return {
                "status": "error",
                "code": 400,
                "message": "class_subject_ids must be a list",
                "data": []
            }

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 1️⃣ Get user_id
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

        # 2️⃣ Get academic profile
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

        # 3️⃣ Validate class_subject_ids exist
        format_strings = ','.join(['%s'] * len(class_subject_ids))
        cursor.execute(f"""
            SELECT id FROM class_subjects
            WHERE id IN ({format_strings})
        """, tuple(class_subject_ids))

        valid_ids = [row["id"] for row in cursor.fetchall()]

        if len(valid_ids) != len(class_subject_ids):
            conn.close()
            return {
                "status": "error",
                "code": 400,
                "message": "One or more class_subject_ids are invalid",
                "data": []
            }

        # 4️⃣ Delete previous selections
        cursor.execute("""
            DELETE FROM student_selected_subjects
            WHERE profile_id = %s
        """, (profile_id,))

        # 5️⃣ Insert new selections
        for cs_id in valid_ids:
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
            "message": "Student subjects saved successfully",
            "data": {
                "profile_id": profile_id,
                "selected_subject_count": len(valid_ids)
            }
        }

    except Exception as e:
        return {
            "status": "error",
            "code": 500,
            "message": str(e),
            "data": []
        }  