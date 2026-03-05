from flask import request, jsonify
import pymysql
from database.config import MYSQL_CONFIG


def submit_test():

    try:

        data = request.json
        attempt_id = data.get("attempt_id")

        connection = pymysql.connect(**MYSQL_CONFIG)
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        cursor.callproc("sp_submit_test", (attempt_id,))
        result = cursor.fetchall()

        connection.commit()

        cursor.close()
        connection.close()

        return jsonify({
            "status": True,
            "statuscode": 200,
            "data": result[0] if result else None,
            "message": "Test submitted successfully"
        }), 200

    except Exception as e:

        return jsonify({
            "status": False,
            "statuscode": 500,
            "data": None,
            "message": str(e)
        }), 500

