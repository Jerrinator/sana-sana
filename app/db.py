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

    def _get_collection(self, env_var_key_or_default: str):
        if not self.database:
            return None

        # Map known default fallback names / env keys to actual environment variable names
        env_map = {
            "bhlr_admin": "COLLECTION_ADMIN",
            "COLLECTION_ADMIN": "COLLECTION_ADMIN",
            "SiteContent": "COLLECTION_SITE_CONTENT",
            "COLLECTION_SITE_CONTENT": "COLLECTION_SITE_CONTENT",
            "AdoptablePets": "COLLECTION_MENU_ITEMS",
            "COLLECTION_MENU_ITEMS": "COLLECTION_MENU_ITEMS",
            "HotTips": "COLLECTION_WELLNESS_TIPS",
            "COLLECTION_WELLNESS_TIPS": "COLLECTION_WELLNESS_TIPS",
            "LostFoundPosts": "COLLECTION_COMMUNITY_POSTS",
            "COLLECTION_COMMUNITY_POSTS": "COLLECTION_COMMUNITY_POSTS",
            "LoyaltyCustomers": "COLLECTION_LOYALTY_CUSTOMERS",
            "COLLECTION_LOYALTY_CUSTOMERS": "COLLECTION_LOYALTY_CUSTOMERS",
            "PilatesRoster": "COLLECTION_PILATES_ROSTER",
            "COLLECTION_PILATES_ROSTER": "COLLECTION_PILATES_ROSTER",
        }

        fallback_defaults = {
            "COLLECTION_ADMIN": "sana_admin",
            "COLLECTION_SITE_CONTENT": "sana_site_content",
            "COLLECTION_MENU_ITEMS": "sana_menu_items",
            "COLLECTION_WELLNESS_TIPS": "sana_wellness_tips",
            "COLLECTION_COMMUNITY_POSTS": "sana_community_posts",
            "COLLECTION_LOYALTY_CUSTOMERS": "sana_loyalty_customers",
            "COLLECTION_PILATES_ROSTER": "sana_pilates_roster",
        }

        env_key = env_map.get(env_var_key_or_default, env_var_key_or_default)
        name = os.getenv(env_key, "").strip() if env_key else ""
        if not name:
            name = fallback_defaults.get(env_var_key_or_default, env_var_key_or_default)

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
        default_doc = {
            "id": "main",
            "hero_text": "Heal from within",
            "mission_snapshot": "Sana Sana brings vibrant, plant-powered drinks, organic teas, and reformer pilates to help you heal from within.",
            "about_text_blocks": [
                "Our biggest goal is to make our products and services accessible to everyone, so they can live a healthy life no matter where they are in their journey.",
                "We blend bright ingredients, wellness-first recipes, and a welcoming atmosphere for every guest.",
                "From signature drinks to reformer pilates, every detail is designed to support your wellness rhythm."
            ],
            "footer_text": "Heal from within",
            "banner_image": "",
            "contact_info": {
                "email": "sanasana13075@gmail.com",
                "phone": "Amy Soberanes: 620-255-8142 | Joanna Reyes: 620-430-0525",
                "address": "1307 5th Ave, Dodge City, KS",
                "social": {
                    "facebook": "https://www.facebook.com/p/Sana-Sana-61582517873961/",
                    "instagram": "https://www.instagram.com/sanasana_620",
                    "snapchat": "https://www.snapchat.com/add/sanasana_620"
                }
            },
            "lostfound_preview_enabled": False,
        }
        self.update_site_content(default_doc)

    def _ensure_seed_admin_user(self):
        # Create Amy Soberanes and Joanna Reyes as the sole admin accounts
        admins_data = [
            {
                "email": "amy.soberanes@sanasana.com",
                "first_name": "Amy",
                "last_name": "Soberanes",
                "password": os.getenv("ADMIN_PASSWORD", "change-me-now"),
            },
            {
                "email": "joanna.reyes@sanasana.com",
                "first_name": "Joanna",
                "last_name": "Reyes",
                "password": os.getenv("ADMIN_PASSWORD", "change-me-now"),
            }
        ]

        # Check if environment provided a specific ADMIN_EMAIL override
        env_email = os.getenv("ADMIN_EMAIL", "").strip()
        if env_email and not any(a["email"] == env_email for a in admins_data):
            admins_data.append({
                "email": env_email,
                "first_name": os.getenv("ADMIN_FIRST_NAME", "Admin").strip() or "Admin",
                "last_name": os.getenv("ADMIN_LAST_NAME", "User").strip() or "User",
                "password": os.getenv("ADMIN_PASSWORD", "change-me-now"),
            })

        for admin_info in admins_data:
            email = admin_info["email"]
            existing = self.get_admin_user(email)
            payload = {
                "username": email,
                "password_hash": generate_password_hash(admin_info["password"]),
                "first_name": admin_info["first_name"],
                "last_name": admin_info["last_name"],
                "email": email,
                "role": "admin",
                "permission_level": "full",
                "is_active": True,
                "must_change_password": True,
            }
            if not existing:
                self.create_admin_user(payload)

    # AdoptablePets / MenuItems
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
        collection = self._get_collection("COLLECTION_MENU_ITEMS")
        if not collection:
            return []
        pets = [self._ensure_pet_tracking_fields(collection, pet) for pet in list(collection.find({}, limit=200))]
        if include_adopted:
            return pets
        return [pet for pet in pets if bool(pet.get("needs_adoption", not pet.get("adopted", False)))]

    def get_pet(self, pet_id: str):
        collection = self._get_collection("COLLECTION_MENU_ITEMS")
        if not collection:
            return None
        pet = collection.find_one({"id": pet_id})
        return self._ensure_pet_tracking_fields(collection, pet)

    def create_pet(self, payload: dict):
        collection = self._get_collection("COLLECTION_MENU_ITEMS")
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
        collection = self._get_collection("COLLECTION_MENU_ITEMS")
        if not collection:
            return None
        payload["updated_at"] = datetime.utcnow().isoformat()
        collection.update_one({"id": pet_id}, {"$set": payload})
        return self.get_pet(pet_id)

    def delete_pet(self, pet_id: str):
        collection = self._get_collection("COLLECTION_MENU_ITEMS")
        if not collection:
            return False
        result = collection.delete_one({"id": pet_id})
        return bool(result.deleted_count)

    # LostFoundPosts / CommunityPosts
    def list_lostfound_posts(self, approved_only: bool = False):
        collection = self._get_collection("COLLECTION_COMMUNITY_POSTS")
        if not collection:
            return []
        query = {"approved": True} if approved_only else {}
        return list(collection.find(query, limit=300))

    def get_lostfound_post(self, post_id: str):
        collection = self._get_collection("COLLECTION_COMMUNITY_POSTS")
        if not collection:
            return None
        return collection.find_one({"id": post_id})

    def create_lostfound_post(self, payload: dict):
        collection = self._get_collection("COLLECTION_COMMUNITY_POSTS")
        if not collection:
            return None
        payload["id"] = str(uuid4())
        payload.setdefault("photos", [])
        payload.setdefault("approved", False)
        payload = self._with_default_dates(payload)
        collection.insert_one(payload)
        return payload

    def update_lostfound_post(self, post_id: str, payload: dict):
        collection = self._get_collection("COLLECTION_COMMUNITY_POSTS")
        if not collection:
            return None
        payload["updated_at"] = datetime.utcnow().isoformat()
        collection.update_one({"id": post_id}, {"$set": payload})
        return self.get_lostfound_post(post_id)

    def delete_lostfound_post(self, post_id: str):
        collection = self._get_collection("COLLECTION_COMMUNITY_POSTS")
        if not collection:
            return False
        result = collection.delete_one({"id": post_id})
        return bool(result.deleted_count)

    # HotTips / WellnessTips
    def list_tips(self):
        collection = self._get_collection("COLLECTION_WELLNESS_TIPS")
        if not collection:
            return []
        return list(collection.find({}, limit=200))

    def create_tip(self, payload: dict):
        collection = self._get_collection("COLLECTION_WELLNESS_TIPS")
        if not collection:
            return None
        payload["id"] = str(uuid4())
        payload = self._with_default_dates(payload)
        collection.insert_one(payload)
        return payload

    def update_tip(self, tip_id: str, payload: dict):
        collection = self._get_collection("COLLECTION_WELLNESS_TIPS")
        if not collection:
            return None
        payload["updated_at"] = datetime.utcnow().isoformat()
        collection.update_one({"id": tip_id}, {"$set": payload})
        return collection.find_one({"id": tip_id})

    def delete_tip(self, tip_id: str):
        collection = self._get_collection("COLLECTION_WELLNESS_TIPS")
        if not collection:
            return False
        result = collection.delete_one({"id": tip_id})
        return bool(result.deleted_count)

    # SiteContent
    def get_site_content(self):
        collection = self._get_collection("COLLECTION_SITE_CONTENT")
        if not collection:
            return {
                "id": "main",
                "hero_text": "Heal from within",
                "mission_snapshot": "Sana Sana Cafe & Studio serves fresh wellness drinks, organic teas, and reformer pilates to nourish your mind and body.",
                "about_text_blocks": [
                    "Our biggest goal is to make our products and services accessible to everyone, so they can live a healthy life no matter where they are in their journey."
                ],
                "footer_text": "Heal from within",
                "banner_image": "",
                "contact_info": {
                    "email": "sanasana13075@gmail.com",
                    "phone": "Amy Soberanes: 620-255-8142 | Joanna Reyes: 620-430-0525",
                    "address": "1307 5th Ave, Dodge City, KS",
                    "social": {
                        "facebook": "https://www.facebook.com/p/Sana-Sana-61582517873961/",
                        "instagram": "https://www.instagram.com/sanasana_620",
                        "snapchat": "https://www.snapchat.com/add/sanasana_620"
                    },
                },
                "lostfound_preview_enabled": False,
            }
        doc = collection.find_one({"id": "main"})
        return doc

    def update_site_content(self, payload: dict):
        collection = self._get_collection("COLLECTION_SITE_CONTENT")
        if not collection:
            return payload
        payload["id"] = "main"
        payload["updated_at"] = datetime.utcnow().isoformat()
        collection.update_one({"id": "main"}, {"$set": payload}, upsert=True)
        return self.get_site_content()

    # bhlr_admin / sana_admin
    def list_admin_users(self):
        collection = self._get_collection("COLLECTION_ADMIN")
        if not collection:
            return []
        return list(collection.find({}, limit=200))

    def get_admin_user(self, username: str):
        collection = self._get_collection("COLLECTION_ADMIN")
        if not collection:
            return None
        clean = (username or "").strip().lower()
        if not clean:
            return None
        return (
            collection.find_one({"email": clean})
            or collection.find_one({"username": clean})
            or collection.find_one({"email": (username or "").strip()})
            or collection.find_one({"username": (username or "").strip()})
        )

    def get_admin_user_by_id(self, admin_id: str):
        collection = self._get_collection("COLLECTION_ADMIN")
        if not collection:
            return None
        return collection.find_one({"id": admin_id})

    def create_admin_user(self, payload: dict):
        collection = self._get_collection("COLLECTION_ADMIN")
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
        collection = self._get_collection("COLLECTION_ADMIN")
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
        collection = self._get_collection("COLLECTION_ADMIN")
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

    # Loyalty Customers
    @staticmethod
    def clean_phone(phone: str) -> str:
        if not phone:
            return ""
        return "".join(c for c in str(phone) if c.isdigit())

    def get_customer_by_phone(self, phone_or_email: str):
        collection = self._get_collection("COLLECTION_LOYALTY_CUSTOMERS")
        if not collection:
            print("[DB TRACE] COLLECTION_LOYALTY_CUSTOMERS collection handle is None!", flush=True)
            return None
        raw = (phone_or_email or "").strip()
        cleaned = self.clean_phone(raw)
        lowered = raw.lower()
        if not raw:
            return None

        print(f"[DB TRACE] get_customer_by_phone: raw='{raw}', cleaned='{cleaned}', lowered='{lowered}'", flush=True)

        # Try clean phone, exact phone, or email lookup
        query_list = []
        if cleaned:
            query_list.append({"clean_phone": cleaned})
            query_list.append({"phone": raw})
        if "@" in lowered:
            query_list.append({"email": lowered})

        for q in query_list:
            try:
                doc = collection.find_one(q)
                if doc:
                    print(f"[DB TRACE] Found customer via query {q}: id={doc.get('id')}", flush=True)
                    return doc
            except Exception as e:
                print(f"[DB TRACE] Exception on find_one({q}): {e}", flush=True)

        # Fallback scan across list if Astra API index differs
        print("[DB TRACE] Direct queries returned nothing, running full collection scan fallback...", flush=True)
        try:
            all_custs = list(collection.find({}, limit=500))
            print(f"[DB TRACE] Full scan found {len(all_custs)} total customers in collection.", flush=True)
            for c in all_custs:
                c_clean = self.clean_phone(c.get("phone", ""))
                c_stored_clean = c.get("clean_phone", "")
                c_email = c.get("email", "").strip().lower()
                print(f"[DB TRACE] Comparing against customer: phone='{c.get('phone')}', c_clean='{c_clean}', c_stored_clean='{c_stored_clean}', email='{c_email}'", flush=True)
                if (cleaned and (c_clean == cleaned or c_stored_clean == cleaned)) or ("@" in lowered and c_email == lowered):
                    print(f"[DB TRACE] Matched customer in fallback scan! id={c.get('id')}", flush=True)
                    return c
        except Exception as e:
            print(f"[DB TRACE] Exception during fallback scan: {e}", flush=True)

        print(f"[DB TRACE] No customer matched for '{phone_or_email}'.", flush=True)
        return None

    def get_customer_by_id(self, customer_id: str):
        collection = self._get_collection("COLLECTION_LOYALTY_CUSTOMERS")
        if not collection:
            return None
        return collection.find_one({"id": customer_id})

    def create_customer(self, payload: dict):
        collection = self._get_collection("COLLECTION_LOYALTY_CUSTOMERS")
        if not collection:
            return None

        phone = payload.get("phone", "").strip()
        cleaned = self.clean_phone(phone)
        if not cleaned:
            return None

        if self.get_customer_by_phone(phone):
            return None

        password = payload.get("password", "")
        customer = {
            "id": str(uuid4()),
            "name": payload.get("name", "").strip(),
            "phone": phone,
            "clean_phone": cleaned,
            "email": payload.get("email", "").strip().lower(),
            "password_hash": generate_password_hash(password) if password else "",
            "points": int(payload.get("points", 10)),  # 10 welcome points!
            "reward_tier": "Sana Member",
            "is_active": True,
        }
        customer = self._with_default_dates(customer)
        collection.insert_one(customer)
        return customer

    def list_customers(self):
        collection = self._get_collection("COLLECTION_LOYALTY_CUSTOMERS")
        if not collection:
            return []
        return list(collection.find({}, limit=500))

    def reset_customer_password(self, customer_id: str, new_password: str):
        collection = self._get_collection("COLLECTION_LOYALTY_CUSTOMERS")
        if not collection or not new_password:
            return None
        payload = {
            "password_hash": generate_password_hash(new_password),
            "updated_at": datetime.utcnow().isoformat()
        }
        collection.update_one({"id": customer_id}, {"$set": payload})
        return self.get_customer_by_id(customer_id)

    def delete_customer(self, customer_id: str):
        collection = self._get_collection("COLLECTION_LOYALTY_CUSTOMERS")
        if not collection:
            return False
        result = collection.delete_one({"id": customer_id})
        return bool(result.deleted_count)

    # Pilates Roster Management
    def list_pilates_roster(self, active_only: bool = True):
        collection = self._get_collection("COLLECTION_PILATES_ROSTER")
        if not collection:
            return []
        query = {"status": "Active"} if active_only else {}
        return list(collection.find(query, limit=300))

    def get_pilates_roster_entry(self, entry_id: str):
        collection = self._get_collection("COLLECTION_PILATES_ROSTER")
        if not collection:
            return None
        return collection.find_one({"id": entry_id})

    def create_pilates_signup(self, payload: dict):
        collection = self._get_collection("COLLECTION_PILATES_ROSTER")
        if not collection:
            return None

        phone = payload.get("phone", "").strip()
        email = payload.get("email", "").strip().lower()
        cleaned_phone = self.clean_phone(phone)

        # Check for existing active enrollment
        if cleaned_phone:
            existing = collection.find_one({"clean_phone": cleaned_phone, "status": "Active"})
            if existing:
                return existing

        entry = {
            "id": str(uuid4()),
            "name": payload.get("name", "").strip(),
            "phone": phone,
            "clean_phone": cleaned_phone,
            "email": email,
            "session_type": payload.get("interest") or payload.get("session_type", "Reformer Flow"),
            "notes": payload.get("notes", "").strip(),
            "status": "Active",  # Active (ongoing participant) or Inactive (left class)
            "joined_date": datetime.utcnow().strftime("%Y-%m-%d"),
        }
        entry = self._with_default_dates(entry)
        collection.insert_one(entry)
        return entry

    def update_pilates_roster_status(self, entry_id: str, status: str):
        collection = self._get_collection("COLLECTION_PILATES_ROSTER")
        if not collection:
            return None
        payload = {
            "status": status,
            "updated_at": datetime.utcnow().isoformat()
        }
        collection.update_one({"id": entry_id}, {"$set": payload})
        return self.get_pilates_roster_entry(entry_id)

    def delete_pilates_roster_entry(self, entry_id: str):
        collection = self._get_collection("COLLECTION_PILATES_ROSTER")
        if not collection:
            return False
        result = collection.delete_one({"id": entry_id})
        return bool(result.deleted_count)

    def delete_admin_user(self, admin_id: str):
        collection = self._get_collection("COLLECTION_ADMIN")
        if not collection:
            return False
        result = collection.delete_one({"id": admin_id})
        return bool(result.deleted_count)


db = AstraDB()
