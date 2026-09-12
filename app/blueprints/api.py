import os
import base64
from uuid import uuid4

import requests
from flask import Blueprint, jsonify, request, current_app
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename

from app.auth_utils import login_required
from app.db import db
from app.email_utils import send_email

api_bp = Blueprint("api", __name__, url_prefix="/api")

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}
ASTRA_INDEXED_STRING_LIMIT = 8000
ASTRA_INDEXED_STRING_SAFE_LIMIT = 7600


class ImageUploadError(Exception):
    pass


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _file_to_data_url(file, max_bytes):
    file.stream.seek(0)
    raw = file.stream.read(max_bytes + 1)
    file.stream.seek(0)
    if not raw or len(raw) > max_bytes:
        return None

    mime = file.mimetype if (file.mimetype or "").startswith("image/") else "image/jpeg"
    encoded = base64.b64encode(raw).decode("ascii")
    data_url = f"data:{mime};base64,{encoded}"
    if len(data_url) > ASTRA_INDEXED_STRING_SAFE_LIMIT:
        return None
    return data_url


def _upload_to_cloudinary(file):
    cloud_name = (current_app.config.get("CLOUDINARY_CLOUD_NAME") or "").strip()
    upload_preset = (current_app.config.get("CLOUDINARY_UPLOAD_PRESET") or "").strip()
    upload_folder = (current_app.config.get("CLOUDINARY_UPLOAD_FOLDER") or "bhlr/pets").strip()
    if not cloud_name or not upload_preset:
        return None

    file.stream.seek(0)
    response = requests.post(
        f"https://api.cloudinary.com/v1_1/{cloud_name}/image/upload",
        data={
            "upload_preset": upload_preset,
            "folder": upload_folder,
        },
        files={
            "file": (
                secure_filename(file.filename),
                file.stream,
                file.mimetype or "application/octet-stream",
            )
        },
        timeout=30,
    )
    response.raise_for_status()
    body = response.json()
    return body.get("secure_url") or body.get("url")


def _upload_to_imgbb(file):
    api_key = (current_app.config.get("IMGBB_API_KEY") or "").strip()
    if not api_key:
        return None

    expiration = str(current_app.config.get("IMGBB_EXPIRATION", "") or "").strip()
    data = {
        "key": api_key,
        "name": secure_filename(file.filename),
    }
    if expiration:
        data["expiration"] = expiration

    file.stream.seek(0)
    response = requests.post(
        "https://api.imgbb.com/1/upload",
        data=data,
        files={
            "image": (
                secure_filename(file.filename),
                file.stream,
                file.mimetype or "application/octet-stream",
            )
        },
        timeout=30,
    )
    response.raise_for_status()
    body = response.json() or {}
    if not body.get("success"):
        return None
    payload = body.get("data") or {}
    return payload.get("url") or payload.get("display_url")


def _save_uploaded_files(files):
    uploaded_values = []
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    store_in_astra = bool(current_app.config.get("STORE_IMAGES_IN_ASTRA", False))
    inline_max_bytes = int(current_app.config.get("ASTRA_INLINE_IMAGE_MAX_BYTES", 5600))
    inline_max_bytes = max(1024, min(inline_max_bytes, 5600))
    use_cloudinary = bool(
        (current_app.config.get("CLOUDINARY_CLOUD_NAME") or "").strip()
        and (current_app.config.get("CLOUDINARY_UPLOAD_PRESET") or "").strip()
    )
    use_imgbb = bool((current_app.config.get("IMGBB_API_KEY") or "").strip())
    os.makedirs(upload_folder, exist_ok=True)

    for file in files:
        if not file or not file.filename:
            continue
        if not allowed_file(file.filename):
            continue

        if use_imgbb:
            try:
                remote_url = _upload_to_imgbb(file)
            except requests.RequestException as exc:
                raise ImageUploadError("Image upload to imgbb failed. Please try again.") from exc
            if not remote_url:
                raise ImageUploadError("Image upload to imgbb failed. Check IMGBB_API_KEY and retry.")
            uploaded_values.append(remote_url)
            continue

        if store_in_astra:
            data_url = _file_to_data_url(file, inline_max_bytes)
            if data_url:
                uploaded_values.append(data_url)
                continue

        if use_cloudinary:
            try:
                remote_url = _upload_to_cloudinary(file)
            except requests.RequestException:
                remote_url = None
            if remote_url:
                uploaded_values.append(remote_url)
                continue

        original_name = secure_filename(file.filename)
        unique_name = f"{uuid4()}_{original_name}"
        file_path = os.path.join(upload_folder, unique_name)
        file.save(file_path)
        uploaded_values.append(unique_name)

    return uploaded_values


def _collect_admin_emails():
    override = (current_app.config.get("MAIL_RECIPIENT_OVERRIDE") or "").strip()
    if override:
        forced = []
        for value in override.split(","):
            email = value.strip()
            if email and email not in forced:
                forced.append(email)
        if forced:
            return forced

    recipients = []
    for admin in db.list_admin_users():
        email = (admin.get("email") or "").strip()
        if email and email not in recipients:
            recipients.append(email)

    site_email = ((db.get_site_content() or {}).get("contact_info") or {}).get("email", "")
    site_email = (site_email or "").strip()
    if site_email and site_email not in recipients:
        recipients.append(site_email)

    fallback = (current_app.config.get("ADMIN_EMAIL") or "").strip()
    if fallback and fallback not in recipients:
        recipients.append(fallback)

    return recipients


@api_bp.route("/pets", methods=["GET"])
def list_pets():
    include_adopted = request.args.get("include_adopted", "true").lower() == "true"
    return jsonify(db.list_pets(include_adopted=include_adopted))


@api_bp.route("/pets", methods=["POST"])
@login_required
def create_pet():
    form = request.form
    adopted = form.get("adopted", "false").lower() == "true"
    is_mixed_breed = form.get("is_mixed_breed", "false").lower() == "true"
    needs_adoption_raw = form.get("needs_adoption")
    needs_adoption = (
        needs_adoption_raw.lower() == "true"
        if needs_adoption_raw is not None
        else not adopted
    )
    payload = {
        "name": form.get("name", "").strip(),
        "age": form.get("age", "").strip(),
        "breed": form.get("breed", "").strip(),
        "personality": form.get("personality", "").strip(),
        "medical": form.get("medical", "").strip(),
        "requirements": form.get("requirements", "").strip(),
        "is_mixed_breed": is_mixed_breed,
        "urgent": form.get("urgent", "false").lower() == "true",
        "adopted": adopted,
        "needs_adoption": needs_adoption,
        "featured_order": int(form.get("featured_order", "999") or 999),
    }
    try:
        payload["photos"] = _save_uploaded_files(request.files.getlist("photos"))
    except ImageUploadError as exc:
        return jsonify({"error": str(exc)}), 502

    created = db.create_pet(payload)
    return jsonify(created or {"error": "Database unavailable"}), (201 if created else 503)


@api_bp.route("/pets/<pet_id>", methods=["PUT"])
@login_required
def update_pet(pet_id):
    form = request.form
    existing = db.get_pet(pet_id)
    if not existing:
        return jsonify({"error": "Pet not found"}), 404

    adopted = form.get("adopted", str(existing.get("adopted", False))).lower() == "true"
    is_mixed_breed = form.get("is_mixed_breed", str(existing.get("is_mixed_breed", False))).lower() == "true"
    needs_adoption_raw = form.get("needs_adoption")
    needs_adoption = (
        needs_adoption_raw.lower() == "true"
        if needs_adoption_raw is not None
        else not adopted
    )

    try:
        new_photos = _save_uploaded_files(request.files.getlist("photos"))
    except ImageUploadError as exc:
        return jsonify({"error": str(exc)}), 502
    photos = existing.get("photos", [])
    if form.get("replace_photos", "false").lower() == "true":
        photos = []
    photos.extend(new_photos)

    payload = {
        "name": form.get("name", existing.get("name", "")).strip(),
        "age": form.get("age", existing.get("age", "")).strip(),
        "breed": form.get("breed", existing.get("breed", "")).strip(),
        "personality": form.get("personality", existing.get("personality", "")).strip(),
        "medical": form.get("medical", existing.get("medical", "")).strip(),
        "requirements": form.get("requirements", existing.get("requirements", "")).strip(),
        "is_mixed_breed": is_mixed_breed,
        "urgent": form.get("urgent", str(existing.get("urgent", False))).lower() == "true",
        "adopted": adopted,
        "needs_adoption": needs_adoption,
        "featured_order": int(form.get("featured_order", str(existing.get("featured_order", 999))) or 999),
        "photos": photos,
    }

    updated = db.update_pet(pet_id, payload)
    return jsonify(updated or {"error": "Database unavailable"}), (200 if updated else 503)


@api_bp.route("/pets/<pet_id>", methods=["DELETE"])
@login_required
def delete_pet(pet_id):
    ok = db.delete_pet(pet_id)
    return jsonify({"success": ok}), (200 if ok else 404)


@api_bp.route("/lostfound", methods=["GET"])
def list_lostfound():
    approved_only = request.args.get("approved_only", "true").lower() == "true"
    return jsonify(db.list_lostfound_posts(approved_only=approved_only))


@api_bp.route("/lostfound", methods=["POST"])
def create_lostfound():
    form = request.form
    payload = {
        "poster_name": form.get("poster_name", "").strip(),
        "contact": form.get("contact", "").strip(),
        "location": form.get("location", "").strip(),
        "date": form.get("date", "").strip(),
        "description": form.get("description", "").strip(),
        "approved": False,
    }
    try:
        payload["photos"] = _save_uploaded_files(request.files.getlist("photos"))
    except ImageUploadError as exc:
        return jsonify({"error": str(exc)}), 502

    created = db.create_lostfound_post(payload)
    message = "Submitted for moderation" if created else "Database unavailable"
    return jsonify(created or {"error": message}), (201 if created else 503)


@api_bp.route("/lostfound/<post_id>", methods=["PUT"])
@login_required
def update_lostfound(post_id):
    data = request.get_json(silent=True) or {}
    allowed_keys = {"poster_name", "contact", "location", "date", "description", "approved", "photos"}
    payload = {k: v for k, v in data.items() if k in allowed_keys}
    updated = db.update_lostfound_post(post_id, payload)
    return jsonify(updated or {"error": "Post not found"}), (200 if updated else 404)


@api_bp.route("/lostfound/<post_id>", methods=["DELETE"])
@login_required
def delete_lostfound(post_id):
    ok = db.delete_lostfound_post(post_id)
    return jsonify({"success": ok}), (200 if ok else 404)


@api_bp.route("/tips", methods=["GET"])
def list_tips():
    return jsonify(db.list_tips())


@api_bp.route("/tips", methods=["POST"])
@login_required
def create_tip():
    data = request.get_json(silent=True) or {}
    payload = {
        "title": data.get("title", "").strip(),
        "description": data.get("description", "").strip(),
        "category": data.get("category", "General").strip(),
    }
    created = db.create_tip(payload)
    return jsonify(created or {"error": "Database unavailable"}), (201 if created else 503)


@api_bp.route("/tips/<tip_id>", methods=["PUT"])
@login_required
def update_tip(tip_id):
    data = request.get_json(silent=True) or {}
    payload = {
        "title": data.get("title", "").strip(),
        "description": data.get("description", "").strip(),
        "category": data.get("category", "General").strip(),
    }
    updated = db.update_tip(tip_id, payload)
    return jsonify(updated or {"error": "Tip not found"}), (200 if updated else 404)


@api_bp.route("/tips/<tip_id>", methods=["DELETE"])
@login_required
def delete_tip(tip_id):
    ok = db.delete_tip(tip_id)
    return jsonify({"success": ok}), (200 if ok else 404)


@api_bp.route("/content", methods=["GET"])
def get_content():
    return jsonify(db.get_site_content())


@api_bp.route("/adoption-applications", methods=["POST"])
def submit_adoption_application():
    data = request.get_json(silent=True) or {}
    required_fields = ["applicant_name", "email", "phone", "city_state", "household", "pet_experience", "pet_id", "pet_name"]
    missing = [field for field in required_fields if not str(data.get(field, "")).strip()]
    if missing:
        return jsonify({"error": "Please complete all required fields."}), 400

    recipients = _collect_admin_emails()
    if not recipients:
        return jsonify({"error": "No admin recipient email is configured yet."}), 503

    subject = f"Adoption Application: {data.get('pet_name', '').strip()}"
    text_body = (
        "BHLR Admin Team,\n\n"
        "A new adoption application was submitted.\n\n"
        f"Pet ID: {data.get('pet_id', '').strip()}\n"
        f"Pet Name: {data.get('pet_name', '').strip()}\n"
        f"Pet Breed: {data.get('pet_breed', '').strip()}\n"
        f"Pet Age: {data.get('pet_age', '').strip()}\n\n"
        f"Applicant Name: {data.get('applicant_name', '').strip()}\n"
        f"Applicant Email: {data.get('email', '').strip()}\n"
        f"Applicant Phone: {data.get('phone', '').strip()}\n"
        f"City/State: {data.get('city_state', '').strip()}\n\n"
        "Household/Home Setup:\n"
        f"{data.get('household', '').strip()}\n\n"
        "Prior Pet Experience:\n"
        f"{data.get('pet_experience', '').strip()}\n\n"
        "Additional Notes:\n"
        f"{data.get('notes', '').strip()}\n"
    )

    ok, error = send_email(
        subject=subject,
        recipients=recipients,
        text_body=text_body,
        reply_to=data.get("email", "").strip() or None,
    )
    if not ok:
        return jsonify({"error": error or "Unable to send application email right now."}), 503

    return jsonify({"success": True, "message": "Application sent to BHLR admins."})


@api_bp.route("/contact-messages", methods=["POST"])
def submit_contact_message():
    data = request.get_json(silent=True) or {}
    required_fields = ["name", "email", "message"]
    missing = [field for field in required_fields if not str(data.get(field, "")).strip()]
    if missing:
        return jsonify({"error": "Please fill out required fields."}), 400

    recipients = _collect_admin_emails()
    if not recipients:
        return jsonify({"error": "No admin recipient email is configured yet."}), 503

    subject = f"Contact Form: {data.get('name', '').strip()}"
    text_body = (
        "A new contact form message was submitted.\n\n"
        f"Name: {data.get('name', '').strip()}\n"
        f"Email: {data.get('email', '').strip()}\n"
        f"Phone: {data.get('phone', '').strip()}\n\n"
        "Message:\n"
        f"{data.get('message', '').strip()}\n"
    )

    ok, error = send_email(
        subject=subject,
        recipients=recipients,
        text_body=text_body,
        reply_to=data.get("email", "").strip() or None,
    )
    if not ok:
        return jsonify({"error": error or "Unable to send message email right now."}), 503

    return jsonify({"success": True, "message": "Message sent successfully."})


# Pilates Roster Endpoints
@api_bp.route("/pilates/signup", methods=["POST"])
def pilates_signup():
    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    phone = data.get("phone", "").strip()
    email = data.get("email", "").strip()

    if not name or not phone or not email:
        return jsonify({"error": "Please provide your name, phone number, and email."}), 400

    entry = db.create_pilates_signup(data)
    if not entry:
        return jsonify({"error": "Unable to add to roster right now. Please try again."}), 500

    # Notify admins by email
    recipients = _collect_admin_emails()
    if recipients:
        subject = f"Reformer Pilates Sign-Up: {name}"
        text_body = (
            "A new participant has joined the Reformer Pilates Roster!\n\n"
            f"Name: {name}\n"
            f"Phone: {phone}\n"
            f"Email: {email}\n"
            f"Session Interest: {data.get('interest') or 'Reformer Flow'}\n"
            f"Notes: {data.get('notes', '')}\n"
        )
        send_email(
            subject=subject,
            recipients=recipients,
            text_body=text_body,
            reply_to=email or None,
        )

    return jsonify({"success": True, "entry": entry})


@api_bp.route("/pilates/roster", methods=["GET"])
@login_required
def get_pilates_roster():
    active_only = request.args.get("active_only", "false").lower() == "true"
    roster = db.list_pilates_roster(active_only=active_only)
    return jsonify({"roster": roster})


@api_bp.route("/pilates/roster/<entry_id>/status", methods=["PUT"])
@login_required
def update_pilates_roster_status(entry_id):
    data = request.get_json(silent=True) or {}
    status = data.get("status", "Active").strip()
    if status not in ["Active", "Inactive"]:
        return jsonify({"error": "Status must be 'Active' or 'Inactive'."}), 400

    updated = db.update_pilates_roster_status(entry_id, status)
    if not updated:
        return jsonify({"error": "Entry not found or unable to update."}), 444
    return jsonify({"success": True, "entry": updated})


@api_bp.route("/pilates/roster/<entry_id>", methods=["DELETE"])
@login_required
def delete_pilates_roster_entry(entry_id):
    deleted = db.delete_pilates_roster_entry(entry_id)
    if not deleted:
        return jsonify({"error": "Entry not found."}), 404
    return jsonify({"success": True})


# Customer Loyalty & Password Management Endpoints
@api_bp.route("/admin/customers", methods=["GET"])
@login_required
def get_admin_customers():
    customers = db.list_customers()
    for c in customers:
        if "password_hash" in c:
            c.pop("password_hash", None)
    return jsonify({"customers": customers})


@api_bp.route("/admin/customers/<customer_id>/reset-password", methods=["POST"])
@login_required
def admin_reset_customer_password(customer_id):
    data = request.get_json(silent=True) or {}
    new_password = data.get("password", "").strip()
    if not new_password:
        return jsonify({"error": "New password is required."}), 400

    customer = db.get_customer_by_id(customer_id)
    if not customer:
        return jsonify({"error": "Customer not found."}), 404

    updated = db.reset_customer_password(customer_id, new_password)
    email_sent = False

    # Dispatch email if requested and customer has email
    if data.get("send_email", True) and customer.get("email"):
        subject = "Your Sana Sana Loyalty Rewards Password Has Been Updated"
        text_body = (
            f"Hello {customer.get('name', 'Member')},\n\n"
            f"Your password for your Sana Sana Rewards account ({customer.get('phone')}) has been updated by shop management.\n\n"
            f"Your New Password: {new_password}\n\n"
            "You can now sign in on our website at https://sana-sana-cafe-c6067fd2c0e7.herokuapp.com using your phone number or email.\n\n"
            "Warmly,\n"
            "Sana Sana Team"
        )
        ok, _ = send_email(
            subject=subject,
            recipients=[customer["email"]],
            text_body=text_body
        )
        email_sent = ok

    return jsonify({"success": True, "customer": updated, "email_sent": email_sent})


@api_bp.route("/admin/customers/<customer_id>/send-reset-email", methods=["POST"])
@login_required
def admin_send_reset_email(customer_id):
    customer = db.get_customer_by_id(customer_id)
    if not customer or not customer.get("email"):
        return jsonify({"error": "Customer email not available."}), 400

    # Generate temporary password reset code
    temp_pass = f"Sana{str(uuid4())[:6]}"
    db.reset_customer_password(customer_id, temp_pass)

    subject = "Sana Sana Rewards Password Reset Request"
    text_body = (
        f"Hello {customer.get('name', 'Member')},\n\n"
        f"We received a request to reset your Sana Sana Loyalty Rewards account password.\n\n"
        f"Temporary Password: {temp_pass}\n\n"
        "Please use this password to sign in at https://sana-sana-cafe-c6067fd2c0e7.herokuapp.com\n\n"
        "Warmly,\n"
        "Sana Sana Team"
    )

    ok, error = send_email(
        subject=subject,
        recipients=[customer["email"]],
        text_body=text_body
    )
    if not ok:
        return jsonify({"error": error or "Unable to send reset email."}), 503

    return jsonify({"success": True, "message": f"Password reset email sent to {customer['email']}"})


@api_bp.route("/admin/customers/<customer_id>", methods=["DELETE"])
@login_required
def delete_customer_account(customer_id):
    deleted = db.delete_customer(customer_id)
    if not deleted:
        return jsonify({"error": "Customer not found."}), 404
    return jsonify({"success": True})


@api_bp.route("/content", methods=["PUT"])
@login_required
def update_content():
    data = request.get_json(silent=True) or {}
    current = db.get_site_content() or {}
    payload = {
        "hero_text": data.get("hero_text", current.get("hero_text", "")),
        "mission_snapshot": data.get("mission_snapshot", current.get("mission_snapshot", "")),
        "about_text_blocks": data.get("about_text_blocks", current.get("about_text_blocks", [])),
        "footer_text": data.get("footer_text", current.get("footer_text", "")),
        "contact_info": data.get("contact_info", current.get("contact_info", {})),
        "lostfound_preview_enabled": data.get(
            "lostfound_preview_enabled", current.get("lostfound_preview_enabled", True)
        ),
    }
    updated = db.update_site_content(payload)
    return jsonify(updated)


@api_bp.route("/admin-accounts", methods=["GET"])
@login_required
def list_admin_accounts():
    accounts = db.list_admin_users()
    for account in accounts:
        account.pop("password_hash", None)
    return jsonify(accounts)


@api_bp.route("/admin-accounts", methods=["POST"])
@login_required
def create_admin_account():
    data = request.get_json(silent=True) or {}
    payload = {
        "password_hash": generate_password_hash("change-me-now"),
        "first_name": data.get("first_name", "").strip(),
        "last_name": data.get("last_name", "").strip(),
        "email": data.get("email", "").strip(),
        "role": data.get("role", "admin").strip() or "admin",
        "permission_level": data.get("permission_level", "full").strip() or "full",
        "is_active": data.get("is_active", True),
        "must_change_password": data.get("must_change_password", True),
    }
    created = db.create_admin_user(payload)
    if created:
        created.pop("password_hash", None)
    return jsonify(created or {"error": "Database unavailable"}), (201 if created else 503)


@api_bp.route("/admin-accounts/<admin_id>", methods=["PUT"])
@login_required
def update_admin_account(admin_id):
    data = request.get_json(silent=True) or {}
    existing = db.get_admin_user_by_id(admin_id)
    payload = {
        "first_name": data.get("first_name", ""),
        "last_name": data.get("last_name", ""),
        "email": data.get("email", ""),
        "role": data.get("role", "admin"),
        "permission_level": data.get("permission_level", "full"),
        "is_active": data.get("is_active", True),
        "must_change_password": data.get("must_change_password", existing.get("must_change_password", False) if existing else False),
    }
    updated = db.update_admin_user(admin_id, payload)
    if updated:
        updated.pop("password_hash", None)
    return jsonify(updated or {"error": "Admin not found"}), (200 if updated else 404)


@api_bp.route("/admin-accounts/<admin_id>", methods=["DELETE"])
@login_required
def delete_admin_account(admin_id):
    ok = db.delete_admin_user(admin_id)
    return jsonify({"success": ok}), (200 if ok else 404)
