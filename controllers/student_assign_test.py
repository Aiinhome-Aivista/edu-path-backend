from flask import request, jsonify
import pymysql
import json
from database.config import MYSQL_CONFIG


def create_student_test():

    try:

        data = request.json

        subject_id = data.get("subject_id")
        chapter_ids = data.get("chapter_ids")
        topic_ids = data.get("topic_ids")
        test_name = data.get("test_name")
        total_questions = data.get("total_questions")
        duration_minutes = data.get("duration_minutes")
        difficulty_level = data.get("difficulty_level")
        due_date = data.get("due_date")

        connection = pymysql.connect(**MYSQL_CONFIG)
        cursor = connection.cursor()

        cursor.callproc(
            "sp_create_student_test",
            (
                subject_id,
                json.dumps(chapter_ids),
                json.dumps(topic_ids),
                test_name,
                total_questions,
                duration_minutes,
                difficulty_level,
                due_date
            )
        )

        connection.commit()

        result = cursor.fetchall()
        test_id = result[0][0] if result else None
        cursor.close()
        connection.close()

        return jsonify({
            "status": True,
            "statuscode": 200,
            "data": {
                "test_id": test_id    
            },
            "message": "Student test created successfully"
        }), 200

    except Exception as e:

        return jsonify({
            "status": False,
            "statuscode": 500,
            "data": None,
            "message": str(e)
        }), 500 
