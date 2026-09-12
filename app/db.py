import os
from datetime import datetime
from uuid import uuid4

from astrapy import DataAPIClient
from werkzeug.security import generate_password_hash


class AstraDB:
    def __init__(self):
        self.database = None

    def _is_placeholder(self, value: str) -> bool:
        lowered = (value or "").strip().lower()
        if not lowered:
            return True
        return (
            "<" in lowered
            or ">" in lowered
            or "..." in lowered
            or lowered == "change-me"
        )

    def init_app(self, app):
        endpoint = os.getenv("ASTRA_DB_API_ENDPOINT", "")
        token = os.getenv("ASTRA_DB_APPLICATION_TOKEN", "")
        keyspace = os.getenv("ASTRA_DB_KEYSPACE", "")

        if self._is_placeholder(endpoint) or self._is_placeholder(token):
            self.database = None
        else:
            client = DataAPIClient(token)
            try:
                # Keep running with no DB if Astra client options differ by version.
                if self._is_placeholder(keyspace):
                    self.database = client.get_database_by_api_endpoint(endpoint)
                else:
                    try:
                        self.database = client.get_database_by_api_endpoint(endpoint, keyspace=keyspace)
                    except TypeError:
                        self.database = client.get_database_by_api_endpoint(endpoint)
            except Exception:
                self.database = None

        self._ensure_default_content()
        self._ensure_seed_admin_user()

    def _get_collection(self, name: str):
        if not self.database:
            return None
        try:
            existing = self.database.list_collection_names()
            if name not in existing:
                self.database.create_collection(name)
        except Exception:
            # If existence checks are unavailable, return the collection handle
            # and let callers handle operation-level errors.
            pass
        return self.database.get_collection(name)

    def _with_default_dates(self, document: dict):
        now = datetime.utcnow().isoformat()
        document.setdefault("created_at", now)
        document["updated_at"] = now
        return document

    def _ensure_default_content(self):
        content = self.get_site_content()
        if not content:
            default_doc = {
                "id": "main",
                "hero_text": "Fresh wellness, made for everyday balance.",
                "mission_snapshot": "Sana Sana brings vibrant, plant-powered drinks, nourishing bowls, and feel-good rituals to your daily routine.",
                "about_text_blocks": [
                    "We blend bright ingredients, wellness-first recipes, and a welcoming atmosphere for every guest.",
                    "From signature juices to nourishing bowls, every detail is designed to support a better rhythm of life."
                ],
                "footer_text": "Sana Sana | Fresh wellness for everyday life",
                "banner_image": "",
                "contact_info": {
                    "email": "hello@sanasanawellness.com",
                    "phone": "(555) 123-4567",
                    "address": "123 Wellness Lane, Suite 200",
                    "social": {
                        "facebook": "https://www.facebook.com",
                        "instagram": "https://www.instagram.com"
                    }
                },
                "lostfound_preview_enabled": False,
            }
            self.update_site_content(default_doc)

    def _ensure_seed_admin_user(self):
        email = os.getenv("ADMIN_EMAIL", "").strip()
        password = os.getenv("ADMIN_PASSWORD", "")
        if not email or not password:
            return

        first_name = os.getenv("ADMIN_FIRST_NAME", "Admin").strip() or "Admin"
        last_name = os.getenv("ADMIN_LAST_NAME", "User").strip() or "User"

        existing = self.get_admin_user(email)
        payload = {
            "username": email,
            "password_hash": generate_password_hash(password),
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "role": "admin",
            "permission_level": "full",
            "is_active": True,
            "must_change_password": True,
        }
        if existing:
            missing_fields = [
                "first_name",
                "last_name",
                "email",
                "role",
                "permission_level",
                "is_active",
                "must_change_password",
            ]
            if existing.get("username") != email or any(field not in existing or existing.get(field) in (None, "") for field in missing_fields):
                self.update_admin_user(existing.get("id"), payload)
            return

        self.create_admin_user(payload)

    # AdoptablePets
    def _generate_pet_gallery_id(self):
        return f"PET-{str(uuid4())[:8].upper()}"

    def _ensure_pet_tracking_fields(self, collection, pet: dict):
        if not pet:
            return pet

        updates = {}

        gallery_id = (pet.get("gallery_id") or "").strip()
        if not gallery_id:
            gallery_id = self._generate_pet_gallery_id()
            pet["gallery_id"] = gallery_id
            updates["gallery_id"] = gallery_id

        if "needs_adoption" not in pet:
            needs_adoption = not bool(pet.get("adopted", False))
            pet["needs_adoption"] = needs_adoption
            updates["needs_adoption"] = needs_adoption

        if "is_mixed_breed" not in pet:
            pet["is_mixed_breed"] = False
            updates["is_mixed_breed"] = False

        pet_id = pet.get("id")
        if collection and pet_id and updates:
            updates["updated_at"] = datetime.utcnow().isoformat()
            collection.update_one(
                {"id": pet_id},
                {"$set": updates},
            )
        return pet

    def list_pets(self, include_adopted: bool = True):
        collection = self._get_collection("AdoptablePets")
        if not collection:
            return []
        pets = [self._ensure_pet_tracking_fields(collection, pet) for pet in list(collection.find({}, limit=200))]
        if include_adopted:
            return pets
        return [pet for pet in pets if bool(pet.get("needs_adoption", not pet.get("adopted", False)))]

    def get_pet(self, pet_id: str):
        collection = self._get_collection("AdoptablePets")
        if not collection:
            return None
        pet = collection.find_one({"id": pet_id})
        return self._ensure_pet_tracking_fields(collection, pet)

    def create_pet(self, payload: dict):
        collection = self._get_collection("AdoptablePets")
        if not collection:
            return None
        payload["id"] = str(uuid4())
        payload["gallery_id"] = (payload.get("gallery_id") or self._generate_pet_gallery_id()).strip()
        payload.setdefault("urgent", False)
        payload.setdefault("adopted", False)
        payload.setdefault("needs_adoption", not bool(payload.get("adopted", False)))
        payload.setdefault("is_mixed_breed", False)
        payload.setdefault("photos", [])
        payload.setdefault("featured_order", 999)
        payload = self._with_default_dates(payload)
        collection.insert_one(payload)
        return payload

    def update_pet(self, pet_id: str, payload: dict):
        collection = self._get_collection("AdoptablePets")
        if not collection:
            return None
        payload["updated_at"] = datetime.utcnow().isoformat()
        collection.update_one({"id": pet_id}, {"$set": payload})
        return self.get_pet(pet_id)

    def delete_pet(self, pet_id: str):
        collection = self._get_collection("AdoptablePets")
        if not collection:
            return False
        result = collection.delete_one({"id": pet_id})
        return bool(result.deleted_count)

    # LostFoundPosts
    def list_lostfound_posts(self, approved_only: bool = False):
        collection = self._get_collection("LostFoundPosts")
        if not collection:
            return []
        query = {"approved": True} if approved_only else {}
        return list(collection.find(query, limit=300))

    def get_lostfound_post(self, post_id: str):
        collection = self._get_collection("LostFoundPosts")
        if not collection:
            return None
        return collection.find_one({"id": post_id})

    def create_lostfound_post(self, payload: dict):
        collection = self._get_collection("LostFoundPosts")
        if not collection:
            return None
        payload["id"] = str(uuid4())
        payload.setdefault("photos", [])
        payload.setdefault("approved", False)
        payload = self._with_default_dates(payload)
        collection.insert_one(payload)
        return payload

    def update_lostfound_post(self, post_id: str, payload: dict):
        collection = self._get_collection("LostFoundPosts")
        if not collection:
            return None
        payload["updated_at"] = datetime.utcnow().isoformat()
        collection.update_one({"id": post_id}, {"$set": payload})
        return self.get_lostfound_post(post_id)

    def delete_lostfound_post(self, post_id: str):
        collection = self._get_collection("LostFoundPosts")
        if not collection:
            return False
        result = collection.delete_one({"id": post_id})
        return bool(result.deleted_count)

    # HotTips
    def list_tips(self):
        collection = self._get_collection("HotTips")
        if not collection:
            return []
        return list(collection.find({}, limit=200))

    def create_tip(self, payload: dict):
        collection = self._get_collection("HotTips")
        if not collection:
            return None
        payload["id"] = str(uuid4())
        payload = self._with_default_dates(payload)
        collection.insert_one(payload)
        return payload

    def update_tip(self, tip_id: str, payload: dict):
        collection = self._get_collection("HotTips")
        if not collection:
            return None
        payload["updated_at"] = datetime.utcnow().isoformat()
        collection.update_one({"id": tip_id}, {"$set": payload})
        return collection.find_one({"id": tip_id})

    def delete_tip(self, tip_id: str):
        collection = self._get_collection("HotTips")
        if not collection:
            return False
        result = collection.delete_one({"id": tip_id})
        return bool(result.deleted_count)

    # SiteContent
    def get_site_content(self):
        collection = self._get_collection("SiteContent")
        if not collection:
            return {
                "id": "main",
                "hero_text": "Helping Pets and People Find Their Way Home",
                "mission_snapshot": "Boot Hill Lifeline Rescue is a 501(c)(3) serving Dodge City and nearby communities within a 75-100 mile radius.",
                "about_text_blocks": [],
                "footer_text": "Boot Hill Lifeline Rescue",
                "banner_image": "",
                "contact_info": {
                    "email": "BootHillLifelineRescue@gmail.com",
                    "phone": "620-255-8896",
                    "address": "PO Box 262, Minneola, KS 67863",
                    "social": {
                        "facebook": "https://www.facebook.com/profile.php?id=61590750711751&rdid=3LDJ3rCdvjuY58Sd&share_url=https%3A%2F%2Fwww.facebook.com%2Fshare%2F1D7RDu2rCo%2F#",
                        "instagram": "https://www.instagram.com/boothill.lifeline.rescue"
                    },
                },
                "lostfound_preview_enabled": True,
            }
        doc = collection.find_one({"id": "main"})
        return doc

    def update_site_content(self, payload: dict):
        collection = self._get_collection("SiteContent")
        if not collection:
            return payload
        payload["id"] = "main"
        payload["updated_at"] = datetime.utcnow().isoformat()
        collection.update_one({"id": "main"}, {"$set": payload}, upsert=True)
        return self.get_site_content()

    # bhlr_admin
    def list_admin_users(self):
        collection = self._get_collection("bhlr_admin")
        if not collection:
            return []
        return list(collection.find({}, limit=200))

    def get_admin_user(self, username: str):
        collection = self._get_collection("bhlr_admin")
        if not collection:
            return None
        return collection.find_one({"email": username}) or collection.find_one({"username": username})

    def get_admin_user_by_id(self, admin_id: str):
        collection = self._get_collection("bhlr_admin")
        if not collection:
            return None
        return collection.find_one({"id": admin_id})

    def create_admin_user(self, payload: dict):
        collection = self._get_collection("bhlr_admin")
        if not collection:
            return None
        email = payload.get("email", "").strip()
        if not email:
            return None
        if self.get_admin_user(email):
            return None

        user = {
            "id": str(uuid4()),
            "username": email,
            "password_hash": payload.get("password_hash", ""),
            "first_name": payload.get("first_name", "").strip(),
            "last_name": payload.get("last_name", "").strip(),
            "email": email,
            "role": payload.get("role", "admin").strip() or "admin",
            "permission_level": payload.get("permission_level", "full").strip() or "full",
            "is_active": bool(payload.get("is_active", True)),
            "must_change_password": bool(payload.get("must_change_password", False)),
        }
        user = self._with_default_dates(user)
        collection.insert_one(user)
        return user

    def update_admin_user(self, admin_id: str, payload: dict):
        collection = self._get_collection("bhlr_admin")
        if not collection:
            return None

        existing = self.get_admin_user_by_id(admin_id)
        if not existing:
            return None

        new_email = payload.get("email", existing.get("email", "")).strip()
        if not new_email:
            return None
        username_match = self.get_admin_user(new_email)
        if username_match and username_match.get("id") != admin_id:
            return None

        updated_payload = {
            "username": new_email,
            "first_name": payload.get("first_name", existing.get("first_name", "")).strip(),
            "last_name": payload.get("last_name", existing.get("last_name", "")).strip(),
            "email": new_email,
            "role": payload.get("role", existing.get("role", "admin")).strip() or "admin",
            "permission_level": payload.get("permission_level", existing.get("permission_level", "full")).strip() or "full",
            "is_active": bool(payload.get("is_active", existing.get("is_active", True))),
            "must_change_password": bool(payload.get("must_change_password", existing.get("must_change_password", False))),
        }

        password = payload.get("password", "").strip()
        if password:
            updated_payload["password_hash"] = generate_password_hash(password)

        updated_payload["updated_at"] = datetime.utcnow().isoformat()
        collection.update_one({"id": admin_id}, {"$set": updated_payload})
        return self.get_admin_user_by_id(admin_id)

    def set_admin_password(self, admin_id: str, password: str, must_change_password: bool = False):
        collection = self._get_collection("bhlr_admin")
        if not collection:
            return None

        existing = self.get_admin_user_by_id(admin_id)
        if not existing or not password:
            return None

        updated_payload = {
            "password_hash": generate_password_hash(password),
            "must_change_password": bool(must_change_password),
            "updated_at": datetime.utcnow().isoformat(),
        }
        collection.update_one({"id": admin_id}, {"$set": updated_payload})
        return self.get_admin_user_by_id(admin_id)

    def delete_admin_user(self, admin_id: str):
        collection = self._get_collection("bhlr_admin")
        if not collection:
            return False
        result = collection.delete_one({"id": admin_id})
        return bool(result.deleted_count)


db = AstraDB()
