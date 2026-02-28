from database.db_connection import get_db_connection


def save_student_academic_profile(data):
    try:
        username = data.get("username")
        board_id = data.get("board_id")
        school_id = data.get("school_id")
        class_id = data.get("class_id")
        academic_year = data.get("academic_year")

        if not all([username, board_id, school_id, class_id, academic_year]):
            return {
                "status": "error",
                "code": 400,
                "message": "All fields required",
                "data": []
            }

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 🔹 Get user_id
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

        # 🔹 Check if profile already exists for same academic year
        cursor.execute("""
            SELECT id FROM student_academic_profile
            WHERE user_id = %s AND academic_year = %s
        """, (user_id, academic_year))

        existing = cursor.fetchone()

        if existing:
            # 🔄 Update existing profile
            cursor.execute("""
                UPDATE student_academic_profile
                SET board_id = %s,
                    school_id = %s,
                    class_id = %s,
                    updated_at = NOW()
                WHERE id = %s
            """, (board_id, school_id, class_id, existing["id"]))

            profile_id = existing["id"]
            action = "updated"

        else:
            # ➕ Insert new profile
            cursor.execute("""
                INSERT INTO student_academic_profile
                (user_id, board_id, school_id, class_id, academic_year)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, board_id, school_id, class_id, academic_year))

            profile_id = cursor.lastrowid
            action = "saved"

        conn.commit()
        conn.close()

        return {
            "status": "success",
            "code": 200,
            "message": f"Student academic profile {action} successfully",
            "data": {
                "profile_id": profile_id,
                "user_id": user_id,
                "board_id": board_id,
                "school_id": school_id,
                "class_id": class_id,
                "academic_year": academic_year
            }
        }

    except Exception as e:
        return {
            "status": "error",
            "code": 500,
            "message": str(e),
            "data": []
        }