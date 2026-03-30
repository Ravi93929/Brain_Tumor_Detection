import random
from datetime import datetime, timedelta

from werkzeug.security import check_password_hash, generate_password_hash

from config import Config
from database.db import get_db
from services.common import parse_dt


def generate_otp():
    return str(random.randint(100000, 999999))



def create_or_replace_otp(email, otp, purpose, expire_minutes, max_attempts):
    conn = get_db()
    cursor = conn.cursor()

    otp_hash = generate_password_hash(otp)
    now = datetime.now()
    expires_at = (now + timedelta(minutes=expire_minutes)).strftime("%Y-%m-%d %H:%M:%S")
    now_db = now.strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("DELETE FROM otp_codes WHERE email = ? AND purpose = ?", (email, purpose))
    cursor.execute(
        """
        INSERT INTO otp_codes (
            email, otp_hash, purpose, expires_at, attempts_left,
            resend_count, resend_window_start, last_sent_at, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (email, otp_hash, purpose, expires_at, max_attempts, 1, now_db, now_db, now_db),
    )

    conn.commit()
    conn.close()



def can_resend_otp(email, purpose):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT resend_count, resend_window_start, last_sent_at
        FROM otp_codes
        WHERE email = ? AND purpose = ?
        ORDER BY id DESC LIMIT 1
        """,
        (email, purpose),
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        return True, ""

    resend_count, resend_window_start, last_sent_at = row
    now = datetime.now()

    if last_sent_at:
        seconds_since_last = (now - parse_dt(last_sent_at)).total_seconds()
        if seconds_since_last < Config.OTP_RESEND_COOLDOWN_SECONDS:
            wait_seconds = int(Config.OTP_RESEND_COOLDOWN_SECONDS - seconds_since_last)
            return False, f"Wait {wait_seconds} seconds before requesting another OTP."

    if resend_window_start:
        window_start = parse_dt(resend_window_start)
        if now - window_start <= timedelta(minutes=Config.OTP_RESEND_WINDOW_MINUTES):
            if resend_count >= Config.OTP_MAX_RESEND_PER_WINDOW:
                return False, "Too many OTP resend requests. Try again later."

    return True, ""



def resend_otp_record_update(email, purpose, new_otp, expire_minutes, max_attempts):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT resend_count, resend_window_start
        FROM otp_codes
        WHERE email = ? AND purpose = ?
        ORDER BY id DESC LIMIT 1
        """,
        (email, purpose),
    )
    row = cursor.fetchone()

    now = datetime.now()
    now_db = now.strftime("%Y-%m-%d %H:%M:%S")
    expires_at = (now + timedelta(minutes=expire_minutes)).strftime("%Y-%m-%d %H:%M:%S")
    otp_hash = generate_password_hash(new_otp)

    resend_count = 1
    resend_window_start = now_db

    if row:
        old_count, old_window_start = row
        if old_window_start and now - parse_dt(old_window_start) <= timedelta(minutes=Config.OTP_RESEND_WINDOW_MINUTES):
            resend_count = old_count + 1
            resend_window_start = old_window_start

    cursor.execute("DELETE FROM otp_codes WHERE email = ? AND purpose = ?", (email, purpose))
    cursor.execute(
        """
        INSERT INTO otp_codes (
            email, otp_hash, purpose, expires_at, attempts_left,
            resend_count, resend_window_start, last_sent_at, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (email, otp_hash, purpose, expires_at, max_attempts, resend_count, resend_window_start, now_db, now_db),
    )

    conn.commit()
    conn.close()



def verify_hashed_otp(email, purpose, user_otp):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, otp_hash, expires_at, attempts_left
        FROM otp_codes
        WHERE email = ? AND purpose = ?
        ORDER BY id DESC LIMIT 1
        """,
        (email, purpose),
    )
    row = cursor.fetchone()

    if not row:
        conn.close()
        return False, "No OTP found. Request a new one."

    otp_id, otp_hash, expires_at, attempts_left = row
    now = datetime.now()

    if now > parse_dt(expires_at):
        cursor.execute("DELETE FROM otp_codes WHERE id = ?", (otp_id,))
        conn.commit()
        conn.close()
        return False, "OTP expired. Request a new one."

    if attempts_left <= 0:
        conn.close()
        return False, "Too many wrong attempts. Request a new OTP."

    if not check_password_hash(otp_hash, user_otp):
        attempts_left -= 1
        cursor.execute("UPDATE otp_codes SET attempts_left = ? WHERE id = ?", (attempts_left, otp_id))
        conn.commit()
        conn.close()
        return False, f"Invalid OTP. Attempts left: {attempts_left}"

    cursor.execute("DELETE FROM otp_codes WHERE id = ?", (otp_id,))
    conn.commit()
    conn.close()
    return True, "OTP verified successfully."
