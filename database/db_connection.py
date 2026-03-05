import mysql.connector
from database.config import MYSQL_CONFIG

def get_db_connection():
    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        return connection
    except mysql.connector.Error as err:
        print("Database connection error:", err)
        return None
