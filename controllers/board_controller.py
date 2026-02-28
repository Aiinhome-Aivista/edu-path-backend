from database.db_connection import get_db_connection


def get_boards():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, name
            FROM education_boards
            WHERE is_active = 1
            ORDER BY name ASC
        """)

        boards = cursor.fetchall()
        conn.close()

        return {
            "status": "success",
            "code": 200,
            "message": "Boards fetched successfully",
            "data": boards
        }

    except Exception as e:
        return {
            "status": "error",
            "code": 500,
            "message": str(e),
            "data": []
        }