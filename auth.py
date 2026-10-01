import sqlite3

from database import get_connection


def login(username, password):
    """
    Memeriksa username dan password
    dari database Risolcu.
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, username, role
        FROM users
        WHERE username = ?
        AND password = ?
    """, (username, password))

    user = cursor.fetchone()

    connection.close()

    if user:
        return {
            "id": user["id"],
            "username": user["username"],
            "role": user["role"]
        }

    return None