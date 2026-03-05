from flask import request, jsonify
import pymysql
from database.config import MYSQL_CONFIG


def get_student_test_questions():

    try:

        data = request.json
        test_id = data.get("test_id")

        connection = pymysql.connect(**MYSQL_CONFIG)
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        cursor.callproc("sp_get_student_test_questions", (test_id,))
        result = cursor.fetchall()

        cursor.close()
        connection.close()

        if not result:
            return jsonify({
                "status": False,
                "statuscode": 404,
                "data": None,
                "message": "Test not found"
            }), 404


        duration = result[0]["duration_minutes"]

        questions = []

        for row in result:

            questions.append({
                "question_id": row["question_id"],
                "question_text": row["question_text"],
                "difficulty": row["difficulty"],
                "options": {
                    "a": row["option_a"],
                    "b": row["option_b"],
                    "c": row["option_c"],
                    "d": row["option_d"]
                }
            })

        return jsonify({
            "status": True,
            "statuscode": 200,
            "data": {
                "duration_minutes": duration,
                "questions": questions
            },
            "message": "Questions fetched successfully"
        }), 200


    except Exception as e:

        return jsonify({
            "status": False,
            "statuscode": 500,
            "data": None,
            "message": str(e)
        }), 500

