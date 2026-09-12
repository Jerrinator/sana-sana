from flask import Blueprint, current_app, redirect, render_template, request, url_for

from app.db import db

public_bp = Blueprint("public", __name__)


@public_bp.app_context_processor
def inject_site_data():
    return {"site_content": db.get_site_content(), "service_radius": "75-100 miles"}


@public_bp.route("/")
@public_bp.route("/home")
def home():
    pets = sorted(db.list_pets(include_adopted=False), key=lambda p: p.get("featured_order", 999))[:6]
    tips = db.list_tips()[:4]
    lost_posts = db.list_lostfound_posts(approved_only=True)[:4]
    return render_template(
        "public/home.html",
        title="Home",
        pets=pets,
        tips=tips,
        lost_posts=lost_posts,
    )

@public_bp.route("/about-us")
def about_us():
    return render_template("public/about.html", title="About Us")


@public_bp.route("/about")
def about():
    return redirect(url_for("public.about_us"))


@public_bp.route("/cafe-and-menu")
@public_bp.route("/menu")
def cafe_and_menu():
    pets = db.list_pets(include_adopted=False)
    breed = request.args.get("breed", "").strip().lower()
    urgent = request.args.get("urgent", "").strip().lower()

    if breed:
        pets = [pet for pet in pets if breed in pet.get("breed", "").lower()]
    if urgent == "true":
        pets = [pet for pet in pets if pet.get("urgent")]

    return render_template("public/adopt.html", title="Cafe & Menu", pets=pets)


@public_bp.route("/adopt")
def adopt():
    return redirect(url_for("public.cafe_and_menu"))


@public_bp.route("/adopt/<pet_id>")
def adopt_pet_profile(pet_id):
    pet = db.get_pet(pet_id)
    return render_template("public/adopt_profile.html", title="Pet Profile", pet=pet)


@public_bp.route("/adopt/apply")
def adopt_apply():
    pet_id = request.args.get("pet_id", "").strip()
    pet = db.get_pet(pet_id) if pet_id else None
    admin_emails = []
    for admin in db.list_admin_users():
        email = (admin.get("email") or "").strip()
        if email and email not in admin_emails:
            admin_emails.append(email)

    contact_email = ((db.get_site_content() or {}).get("contact_info") or {}).get("email", "")
    contact_email = (contact_email or "").strip()
    if contact_email and contact_email not in admin_emails:
        admin_emails.append(contact_email)

    page_title = "Adoption Application"
    if pet and pet.get("name"):
        page_title = f"Adopt {pet.get('name')}"

    return render_template(
        "public/adopt_apply.html",
        title=page_title,
        pet=pet,
        admin_emails=admin_emails,
    )


@public_bp.route("/lostfound")
def lostfound():
    posts = db.list_lostfound_posts(approved_only=True)
    return render_template("public/lostfound.html", title="Lost & Found", posts=posts)


@public_bp.route("/donate")
def donate():
    return render_template("public/donate.html", title="Donate", payment_link=current_app.config["PAYMENT_LINK"])

@public_bp.route("/pilates-studio")
@public_bp.route("/studio")
def pilates_studio():
    return render_template("public/volunteer.html", title="Pilates Studio")


@public_bp.route("/volunteer")
def volunteer():
    return redirect(url_for("public.pilates_studio"))


@public_bp.route("/tips")
def tips():
    tips_list = db.list_tips()
    return render_template("public/tips.html", title="Hot Tips", tips=tips_list)

@public_bp.route("/contact-and-location")
def contact_and_location():
    return render_template("public/contact.html", title="Contact & Location")


@public_bp.route("/contact")
def contact():
    return redirect(url_for("public.contact_and_location"))
