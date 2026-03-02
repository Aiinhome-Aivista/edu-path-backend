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

def get_student_full_profile_secure(current_user):
    """
    current_user: ডেকোরেটর থেকে ডিকোড করা ডেটা (user_id, username ইত্যাদি)
    """
    try:
        user_id = current_user.get("user_id")
        username = current_user.get("username")

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Get academic profile
        cursor.execute("""
    SELECT 
        sap.id AS profile_id,
        sap.academic_year,
        b.id AS board_id, b.name AS board_name,
        s.id AS school_id, s.name AS school_name,
        c.id AS class_id, c.name AS class_name,
        um.full_name  -- 🔹 এই কলামটি যোগ করুন
    FROM student_academic_profile sap
    JOIN user_master um ON sap.user_id = um.user_id -- 🔹 টেবিল জয়েন করুন
    JOIN education_boards b ON sap.board_id = b.id
    JOIN schools s ON sap.school_id = s.id
    JOIN classes c ON sap.class_id = c.id
    WHERE sap.user_id = %s
    AND sap.is_active = 1
    LIMIT 1
""", (user_id,))

        profile = cursor.fetchone()

        if not profile:
            conn.close()
            return {
                "status": "error",
                "code": 404,
                "message": "Academic profile not found",
                "data": {}
            }

        profile_id = profile["profile_id"]

        # Get subjects
        cursor.execute("""
            SELECT 
                sub.id AS subject_id,
                sub.name AS subject_name
            FROM student_selected_subjects ss
            JOIN class_subjects cs ON ss.class_subject_id = cs.id
            JOIN subjects sub ON cs.subject_id = sub.id
            WHERE ss.profile_id = %s
        """, (profile_id,))

        subjects = cursor.fetchall()
        conn.close()

        return {
            "status": "success",
            "code": 200,
            "message": "Student dashboard fetched successfully",
            "data": {
                "username": username,
                "full_name": profile["full_name"],  
                "academic_year": profile["academic_year"],
                "board": {"id": profile["board_id"], "name": profile["board_name"]},
                "school": {"id": profile["school_id"], "name": profile["school_name"]},
                "class": {"id": profile["class_id"], "name": profile["class_name"]},
                "subjects": subjects
            }
        }

    except Exception as e:
        return {
            "status": "error",
            "code": 500,
            "message": str(e),
            "data": {}
        }