from werkzeug.security import check_password_hash, generate_password_hash

from database.db import get_db
from services.common import now_str


def create_user(fullname, email, password):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO users (fullname, email, password, is_verified, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (fullname, email, generate_password_hash(password), 0, now_str()),
    )
    conn.commit()
    conn.close()


def get_user_by_email(email):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, fullname, email, password, is_verified FROM users WHERE email = ?",
        (email,),
    )
    user = cursor.fetchone()
    conn.close()
    return user


def validate_user_password(user, password):
    return check_password_hash(user[3], password)


def mark_user_verified(email):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_verified = 1 WHERE email = ?", (email,))
    conn.commit()
    conn.close()


def update_password(email, new_password):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET password = ? WHERE email = ?",
        (generate_password_hash(new_password), email),
    )
    conn.commit()
    conn.close()


def user_exists(email):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()
    return row is not None