from flask import request, jsonify
import pymysql
from database.config import MYSQL_CONFIG


def create_attempt():

    try:

        data = request.json
        test_id = data.get("test_id")

        connection = pymysql.connect(**MYSQL_CONFIG)
        cursor = connection.cursor()

        cursor.callproc("sp_create_attempt", (test_id,))
        result = cursor.fetchall()

        attempt_id = result[0][0] if result else None

        connection.commit()

        cursor.close()
        connection.close()

        return jsonify({
            "status": True,
            "statuscode": 200,
            "data": {
                "attempt_id": attempt_id
            },
            "message": "Attempt created successfully"
        }), 200

    except Exception as e:

        return jsonify({
            "status": False,
            "statuscode": 500,
            "data": None,
            "message": str(e)
        }), 500

