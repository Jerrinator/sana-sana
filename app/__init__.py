import os

from flask import Flask
from dotenv import load_dotenv

from app.blueprints.public import public_bp
from app.blueprints.admin import admin_bp
from app.blueprints.api import api_bp
from app.blueprints.auth import auth_bp
from app.db import db
from app.email_utils import init_mail


def create_app() -> Flask:
    load_dotenv()

    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "dev-secret-key")
    app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024
    app.config["UPLOAD_FOLDER"] = os.path.join(app.static_folder, "uploads")
    app.config["PAYMENT_LINK"] = os.getenv("PAYMENT_LINK", "https://example.org/donate")
    app.config["ADMIN_EMAIL"] = os.getenv("ADMIN_EMAIL", "")
    app.config["CLOUDINARY_CLOUD_NAME"] = os.getenv("CLOUDINARY_CLOUD_NAME", "")
    app.config["CLOUDINARY_UPLOAD_PRESET"] = os.getenv("CLOUDINARY_UPLOAD_PRESET", "")
    app.config["CLOUDINARY_UPLOAD_FOLDER"] = os.getenv("CLOUDINARY_UPLOAD_FOLDER", "bhlr/pets")
    app.config["IMGBB_API_KEY"] = os.getenv("IMGBB_API_KEY", "")
    app.config["IMGBB_EXPIRATION"] = os.getenv("IMGBB_EXPIRATION", "")
    app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER", "")
    app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT", "587"))
    app.config["MAIL_USE_TLS"] = os.getenv("MAIL_USE_TLS", "true").lower() in {"1", "true", "on", "yes"}
    app.config["MAIL_USE_SSL"] = os.getenv("MAIL_USE_SSL", "false").lower() in {"1", "true", "on", "yes"}
    app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME", "")
    app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD", "")
    app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_DEFAULT_SENDER", "")
    app.config["MAIL_RECIPIENT_OVERRIDE"] = os.getenv("MAIL_RECIPIENT_OVERRIDE", "")
    app.config["MAIL_SEND_SYNC"] = os.getenv("MAIL_SEND_SYNC", "false").lower() == "true"
    app.config["STORE_IMAGES_IN_ASTRA"] = os.getenv("STORE_IMAGES_IN_ASTRA", "false").lower() == "true"
    try:
        app.config["ASTRA_INLINE_IMAGE_MAX_BYTES"] = int(os.getenv("ASTRA_INLINE_IMAGE_MAX_BYTES", "5600"))
    except ValueError:
        app.config["ASTRA_INLINE_IMAGE_MAX_BYTES"] = 5600

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    init_mail(app)
    db.init_app(app)

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    return app
