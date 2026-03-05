from flask import request, jsonify
from database.db_connection import get_db_connection


def get_test_details():
    try:
        # Get the test_id from the URL query parameters
        test_id = request.args.get("test_id")
       
        if not test_id:
            return {
                "status": "error",
                "code": 400,
                "message": "Please provide a test_id",
                "data": []
            }


        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)


        # SQL JOIN based on subject_id = id, filtered by the specific test_id
        query = """
            SELECT *
            FROM student_tests st
            JOIN subjects s ON st.subject_id = s.id
            WHERE st.id = %s
        """
       
        # Execute the query passing the test_id
        cursor.execute(query, (test_id,))
        test_data = cursor.fetchall()
       
        conn.close()


        return {
            "status": "success",
            "code": 200,
            "message": "Test details fetched successfully",
            "data": test_data
        }


    except Exception as e:
        return {
            "status": "error",
            "code": 500,
            "message": str(e),
            "data": []
        }

