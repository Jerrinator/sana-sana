from flask import Blueprint, render_template, session

from app.auth_utils import login_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("")
@login_required
def dashboard():
    return render_template(
        "admin/dashboard.html",
        title="Admin Dashboard",
        admin_user=session.get("admin_user"),
        admin_profile=session.get("admin_profile", {}),
    )


@admin_bp.route("/pets")
@login_required
def pets_manager():
    return render_template("admin/pets_manager.html", title="Admin Pets Manager")


@admin_bp.route("/pet-registry")
@login_required
def pet_registry():
    return render_template("admin/pet_registry.html", title="Pet Registry")


@admin_bp.route("/lostfound")
@login_required
def lostfound_manager():
    return render_template("admin/lostfound_manager.html", title="Admin Lost & Found Moderation")


@admin_bp.route("/content")
@login_required
def content_manager():
    return render_template("admin/content_manager.html", title="Admin Site Content Editor")


@admin_bp.route("/accounts")
@login_required
def accounts_manager():
    return render_template("admin/accounts_manager.html", title="Admin Accounts Manager")


@admin_bp.route("/pilates-roster")
@login_required
def pilates_roster_manager():
    return render_template("admin/pilates_roster.html", title="Pilates Class Roster Manager")


@admin_bp.route("/customers")
@login_required
def customers_manager():
    return render_template("admin/customers_manager.html", title="Customer Loyalty & Password Manager")
