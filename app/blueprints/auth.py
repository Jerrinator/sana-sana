from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from app.db import db

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/admin/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
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


@auth_bp.route("/admin/logout")
def logout():
    session.pop("admin_user", None)
    session.pop("admin_profile", None)
    return redirect(url_for("auth.login"))


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
