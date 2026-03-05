from flask import request, jsonify
import pymysql
from database.config import MYSQL_CONFIG


def save_student_answer():

    try:

        data = request.json

        attempt_id = data.get("attempt_id")
        question_id = data.get("question_id")
        answer = data.get("answer")

        connection = pymysql.connect(**MYSQL_CONFIG)
        cursor = connection.cursor()

        cursor.callproc(
            "sp_save_student_answer",
            (
                attempt_id,
                question_id,
                answer
            )
        )

        connection.commit()

        cursor.close()
        connection.close()

        return jsonify({
            "status": True,
            "statuscode": 200,
            "data": None,
            "message": "Answer saved successfully"
        }), 200


    except Exception as e:

        return jsonify({
            "status": False,
            "statuscode": 500,
            "data": None,
            "message": str(e)
        }), 500

