from database.db_connection import get_db_connection


def get_schools_by_board(data):
    try:
        board_id = data.get("board_id")

        if not board_id:
            return {
                "status": "error",
                "code": 400,
                "message": "board_id is required",
                "data": []
            }

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, name
            FROM schools
            WHERE board_id = %s AND is_active = 1
            ORDER BY name ASC
        """, (board_id,))

        schools = cursor.fetchall()
        conn.close()

        return {
            "status": "success",
            "code": 200,
            "message": "All Schools fetched successfully",
            "data": schools
        }

    except Exception as e:
        return {
            "status": "error",
            "code": 500,
            "message": str(e),
            "data": []
        }