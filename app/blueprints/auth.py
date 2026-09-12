from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for
from itsdangerous import URLSafeTimedSerializer
from werkzeug.security import check_password_hash

from app.db import db
from app.email_utils import send_email

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/admin/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = db.get_admin_user(email)
        if user and user.get("is_active", True) and check_password_hash(user.get("password_hash", ""), password):
            session["admin_user"] = user.get("email", email)
            session["admin_profile"] = {
                "id": user.get("id"),
                "username": user.get("email", user.get("username", email)),
                "first_name": user.get("first_name", ""),
                "last_name": user.get("last_name", ""),
                "email": user.get("email", ""),
                "role": user.get("role", "admin"),
                "permission_level": user.get("permission_level", "full"),
                "must_change_password": bool(user.get("must_change_password", False)),
            }
            if session["admin_profile"]["must_change_password"]:
                return redirect(url_for("auth.change_password"))
            return redirect(url_for("admin.dashboard"))

        flash("Invalid email or password.", "error")

    return render_template("admin/login.html", title="Admin Login")


@auth_bp.route("/logout")
@auth_bp.route("/admin/logout")
def logout():
    session.pop("admin_user", None)
    session.pop("admin_profile", None)
    session.pop("customer", None)
    flash("You have signed out.", "success")
    return redirect(url_for("public.home"))


@auth_bp.route("/admin/change-password", methods=["GET", "POST"])
def change_password():
    if not session.get("admin_user"):
        return redirect(url_for("auth.login"))

    profile = session.get("admin_profile", {})
    admin_id = profile.get("id")
    if not admin_id:
        return redirect(url_for("auth.logout"))

    if request.method == "POST":
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        user = db.get_admin_user_by_id(admin_id)
        if not user or not check_password_hash(user.get("password_hash", ""), current_password):
            flash("Current password is incorrect.", "error")
        elif not new_password:
            flash("New password is required.", "error")
        elif new_password != confirm_password:
            flash("New password and confirmation do not match.", "error")
        else:
            updated = db.set_admin_password(admin_id, new_password, must_change_password=False)
            if updated:
                session["admin_profile"]["must_change_password"] = False
                flash("Password updated successfully.", "success")
                return redirect(url_for("admin.dashboard"))
            flash("Unable to update password.", "error")

    return render_template(
        "admin/change_password.html",
        title="Change Admin Password",
        admin_profile=profile,
    )


# Customer Loyalty Rewards Authentication
@auth_bp.route("/customer/register", methods=["POST"])
def customer_register():
    name = request.form.get("name", "").strip()
    phone = request.form.get("phone", "").strip()
    password = request.form.get("password", "")
    email = request.form.get("email", "").strip().lower()

    print(f"[AUTH TRACE] Customer register attempt: name='{name}', phone='{phone}', email='{email}'", flush=True)

    if not name or not phone or not email or not password:
        print("[AUTH TRACE] Missing registration fields.", flush=True)
        flash("Please provide your name, phone number, email address, and a password.", "error")
        return redirect(url_for("public.home") + "#rewards")

    cleaned_phone = db.clean_phone(phone)
    if len(cleaned_phone) < 7:
        print(f"[AUTH TRACE] Invalid phone length: cleaned='{cleaned_phone}'", flush=True)
        flash("Please enter a valid phone number.", "error")
        return redirect(url_for("public.home") + "#rewards")

    existing = db.get_customer_by_phone(phone) or db.get_customer_by_phone(email)
    if existing:
        print(f"[AUTH TRACE] Existing customer found on register: id={existing.get('id')}, name='{existing.get('name')}'", flush=True)
        flash("A loyalty account with this phone number or email already exists. Please sign in.", "error")
        return redirect(url_for("public.home") + "#rewards")

    customer = db.create_customer({
        "name": name,
        "phone": phone,
        "password": password,
        "email": email,
        "points": 10  # 10 welcome points!
    })

    if customer:
        session["customer"] = {
            "id": customer["id"],
            "name": customer["name"],
            "phone": customer["phone"],
            "email": customer.get("email", ""),
            "points": customer.get("points", 10),
            "tier": customer.get("reward_tier", "Sana Member")
        }
        print(f"[AUTH TRACE] Customer registration SUCCESS: id={customer['id']}, name='{customer['name']}'", flush=True)
        flash(f"Welcome to Sana Sana Rewards, {customer['name']}! 10 welcome points have been added to your account.", "success")
    else:
        print("[AUTH TRACE] Customer creation returned None.", flush=True)
        flash("Unable to create your rewards account right now. Please try again.", "error")

    return redirect(request.referrer or url_for("public.home"))


@auth_bp.route("/customer/login", methods=["GET", "POST"])
def customer_login():
    target_url = request.referrer or url_for("public.home")
    if request.method == "GET":
        return redirect(target_url)

    phone = request.form.get("phone", "").strip()
    password = request.form.get("password", "")

    print(f"[AUTH TRACE] Customer login attempt: phone/email input='{phone}', password_len={len(password)}", flush=True)

    if not phone or not password:
        print("[AUTH TRACE] Missing phone/email or password input.", flush=True)
        flash("Please provide your phone number or email, and password.", "error")
        return redirect(target_url)

    customer = db.get_customer_by_phone(phone)
    if not customer:
        print(f"[AUTH TRACE] db.get_customer_by_phone('{phone}') returned NONE", flush=True)
        flash("Invalid phone number / email or password.", "error")
        return redirect(target_url)

    print(f"[AUTH TRACE] Found customer: id={customer.get('id')}, name='{customer.get('name')}', phone='{customer.get('phone')}', email='{customer.get('email')}', is_active={customer.get('is_active')}", flush=True)

    if not customer.get("is_active", True):
        print("[AUTH TRACE] Customer account is inactive.", flush=True)
        flash("Invalid phone number / email or password.", "error")
        return redirect(target_url)

    pw_hash = customer.get("password_hash", "")
    pw_match = check_password_hash(pw_hash, password) if pw_hash else False
    print(f"[AUTH TRACE] Password hash present={bool(pw_hash)}, match_result={pw_match}", flush=True)

    if pw_match:
        session["customer"] = {
            "id": customer["id"],
            "name": customer["name"],
            "phone": customer["phone"],
            "email": customer.get("email", ""),
            "points": customer.get("points", 10),
            "tier": customer.get("reward_tier", "Sana Member")
        }
        print(f"[AUTH TRACE] Login SUCCESS for customer '{customer.get('name')}'. Session customer set.", flush=True)
        flash(f"Welcome back, {customer.get('name', 'Member')}!", "success")
    else:
        print("[AUTH TRACE] Password check FAILED.", flush=True)
        flash("Invalid phone number / email or password.", "error")

    return redirect(target_url)


@auth_bp.route("/customer/logout")
def customer_logout():
    session.pop("customer", None)
    flash("You have signed out of your rewards account.", "success")
    return redirect(request.referrer or url_for("public.home"))


# Customer Self-Service Password Reset
@auth_bp.route("/customer/forgot-password", methods=["GET", "POST"])
def customer_forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        if not email:
            flash("Please enter your account email address.", "error")
            return render_template("public/forgot_password.html", title="Forgot Password")

        customer = db.get_customer_by_phone(email)
        if customer and customer.get("email"):
            secret = current_app.config.get("FLASK_SECRET_KEY") or current_app.config.get("SECRET_KEY") or "sana-secret"
            serializer = URLSafeTimedSerializer(secret)
            token = serializer.dumps(customer["id"], salt="customer-reset-token")
            reset_url = url_for("auth.customer_reset_password", token=token, _external=True)

            subject = "Reset Your Sana Sana Loyalty Rewards Password"
            text_body = (
                f"Hello {customer.get('name', 'Member')},\n\n"
                "We received a request to reset the password for your Sana Sana Loyalty Rewards account.\n\n"
                f"Click the link below (or copy and paste it into your browser) to set your new password:\n\n"
                f"{reset_url}\n\n"
                "This reset link will expire in 1 hour.\n\n"
                "If you did not request a password reset, you can safely ignore this email.\n\n"
                "Warmly,\n"
                "Sana Sana Team"
            )
            send_email(
                subject=subject,
                recipients=[customer["email"]],
                text_body=text_body
            )

        flash("If an account matching that email exists, we have sent a password reset link to your email address.", "success")
        return render_template("public/forgot_password.html", title="Forgot Password", sent=True)

    return render_template("public/forgot_password.html", title="Forgot Password")


@auth_bp.route("/customer/reset-password", methods=["GET", "POST"])
def customer_reset_password():
    token = request.args.get("token") or request.form.get("token") or ""
    if not token:
        flash("Invalid or missing password reset link.", "error")
        return redirect(url_for("auth.customer_forgot_password"))

    secret = current_app.config.get("FLASK_SECRET_KEY") or current_app.config.get("SECRET_KEY") or "sana-secret"
    serializer = URLSafeTimedSerializer(secret)
    try:
        customer_id = serializer.loads(token, salt="customer-reset-token", max_age=3600)
    except Exception:
        flash("The password reset link is invalid or has expired. Please request a new link.", "error")
        return redirect(url_for("auth.customer_forgot_password"))

    customer = db.get_customer_by_id(customer_id)
    if not customer:
        flash("Customer account not found.", "error")
        return redirect(url_for("auth.customer_forgot_password"))

    if request.method == "POST":
        new_password = request.form.get("new_password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()

        if not new_password:
            flash("Please enter a new password.", "error")
        elif new_password != confirm_password:
            flash("Passwords do not match.", "error")
        else:
            db.reset_customer_password(customer_id, new_password)
            flash("Your password has been updated successfully! Please sign in with your new password.", "success")
            return redirect(url_for("public.home") + "#rewards")

    return render_template("public/reset_password.html", title="Reset Password", token=token, customer=customer)
