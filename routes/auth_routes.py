from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, session
)
import sqlite3

from services.auth_service import (
    create_user,
    get_user_by_email,
    validate_user_password,
    mark_user_verified,
    update_password,
    user_exists,
)
from services.otp_service import (
    generate_otp,
    create_or_replace_otp,
    verify_hashed_otp,
    can_resend_otp,
    resend_otp_record_update,
)
from services.mail_service import send_email
from config import Config

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        fullname = request.form.get("fullname", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        if not fullname or not email or not password:
            flash("All fields are required.", "danger")
            return redirect(url_for("auth.register"))

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "warning")
            return redirect(url_for("auth.register"))

        try:
            create_user(fullname, email, password)
        except sqlite3.IntegrityError:
            flash("Email already exists. Use another one.", "danger")
            return redirect(url_for("auth.register"))
        except Exception as e:
            flash(f"Registration failed: {str(e)}", "danger")
            return redirect(url_for("auth.register"))

        otp = generate_otp()

        create_or_replace_otp(
            email=email,
            otp=otp,
            purpose="verify",
            expire_minutes=Config.OTP_EXPIRE_MINUTES,
            max_attempts=Config.OTP_MAX_VERIFY_ATTEMPTS,
        )

        try:
            send_email(
                email,
                "NeuroScan AI - Email Verification OTP",
                f"Your OTP is {otp}. It expires in {Config.OTP_EXPIRE_MINUTES} minutes."
            )
        except Exception as e:
            flash(f"User created, but OTP display failed: {str(e)}", "danger")
            return redirect(url_for("auth.register"))

        session["pending_verification_email"] = email
        flash("Registration successful. OTP is shown in terminal.", "success")
        return redirect(url_for("auth.verify_email"))

    return render_template("register.html")


@auth_bp.route("/verify-email", methods=["GET", "POST"])
def verify_email():
    email = session.get("pending_verification_email")

    if not email:
        flash("No pending verification found. Register first.", "warning")
        return redirect(url_for("auth.register"))

    if request.method == "POST":
        otp = request.form.get("otp", "").strip()

        if not otp:
            flash("OTP is required.", "danger")
            return redirect(url_for("auth.verify_email"))

        ok, message = verify_hashed_otp(email, "verify", otp)

        if not ok:
            flash(message, "danger")
            return redirect(url_for("auth.verify_email"))

        mark_user_verified(email)
        session.pop("pending_verification_email", None)
        flash("Email verified successfully. Login now.", "success")
        return redirect(url_for("auth.login"))

    return render_template("verify_email.html", email=email)


@auth_bp.route("/resend-otp/<purpose>")
def resend_otp(purpose):
    if purpose == "verify":
        email = session.get("pending_verification_email")
        expire_minutes = Config.OTP_EXPIRE_MINUTES
        max_attempts = Config.OTP_MAX_VERIFY_ATTEMPTS
        subject = "NeuroScan AI - Verification OTP"
        redirect_endpoint = "auth.verify_email"

    elif purpose == "reset":
        email = session.get("pending_reset_email")
        expire_minutes = Config.RESET_OTP_EXPIRE_MINUTES
        max_attempts = Config.RESET_MAX_VERIFY_ATTEMPTS
        subject = "NeuroScan AI - Password Reset OTP"
        redirect_endpoint = "auth.reset_password_verify"

    else:
        flash("Invalid OTP purpose.", "danger")
        return redirect(url_for("main.home"))

    if not email:
        flash("No pending request found.", "warning")
        return redirect(url_for("main.home"))

    allowed, message = can_resend_otp(email, purpose)

    if not allowed:
        flash(message, "warning")
        return redirect(url_for(redirect_endpoint))

    otp = generate_otp()

    resend_otp_record_update(
        email=email,
        purpose=purpose,
        new_otp=otp,
        expire_minutes=expire_minutes,
        max_attempts=max_attempts,
    )

    try:
        send_email(
            email,
            subject,
            f"Your OTP is {otp}. It expires in {expire_minutes} minutes."
        )
        flash("A new OTP is shown in terminal.", "success")
    except Exception as e:
        flash(f"Failed to generate/display OTP: {str(e)}", "danger")

    return redirect(url_for(redirect_endpoint))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        user = get_user_by_email(email)

        if not user:
            flash("Account not found.", "danger")
            return redirect(url_for("auth.login"))

        if not validate_user_password(user, password):
            flash("Invalid email or password.", "danger")
            return redirect(url_for("auth.login"))

        if user[4] == 0:
            session["pending_verification_email"] = email
            flash("Your email is not verified. Enter the terminal OTP.", "warning")
            return redirect(url_for("auth.verify_email"))

        session["user_id"] = user[0]
        session["fullname"] = user[1]
        session["email"] = user[2]

        flash("Login successful.", "success")
        return redirect(url_for("prediction.predict_page"))

    return render_template("login.html")


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()

        if not email:
            flash("Email is required.", "danger")
            return redirect(url_for("auth.forgot_password"))

        if not user_exists(email):
            flash("No account found with that email.", "danger")
            return redirect(url_for("auth.forgot_password"))

        otp = generate_otp()

        create_or_replace_otp(
            email=email,
            otp=otp,
            purpose="reset",
            expire_minutes=Config.RESET_OTP_EXPIRE_MINUTES,
            max_attempts=Config.RESET_MAX_VERIFY_ATTEMPTS,
        )

        try:
            send_email(
                email,
                "NeuroScan AI - Password Reset OTP",
                f"Your password reset OTP is {otp}. It expires in {Config.RESET_OTP_EXPIRE_MINUTES} minutes."
            )
        except Exception as e:
            flash(f"Failed to generate/display reset OTP: {str(e)}", "danger")
            return redirect(url_for("auth.forgot_password"))

        session["pending_reset_email"] = email
        flash("Password reset OTP is shown in terminal.", "success")
        return redirect(url_for("auth.reset_password_verify"))

    return render_template("forgot_password.html")


@auth_bp.route("/reset-password-verify", methods=["GET", "POST"])
def reset_password_verify():
    email = session.get("pending_reset_email")

    if not email:
        flash("No pending reset request found.", "warning")
        return redirect(url_for("auth.forgot_password"))

    if request.method == "POST":
        otp = request.form.get("otp", "").strip()
        new_password = request.form.get("new_password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()

        if not otp or not new_password or not confirm_password:
            flash("All fields are required.", "danger")
            return redirect(url_for("auth.reset_password_verify"))

        if len(new_password) < 6:
            flash("New password must be at least 6 characters.", "warning")
            return redirect(url_for("auth.reset_password_verify"))

        if new_password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("auth.reset_password_verify"))

        ok, message = verify_hashed_otp(email, "reset", otp)

        if not ok:
            flash(message, "danger")
            return redirect(url_for("auth.reset_password_verify"))

        update_password(email, new_password)
        session.pop("pending_reset_email", None)

        flash("Password reset successful. Login now.", "success")
        return redirect(url_for("auth.login"))

    return render_template("reset_password.html", email=email)


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.home"))