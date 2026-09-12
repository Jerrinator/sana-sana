# Boot Hill Lifeline Rescue

Multi-page Flask website for Boot Hill Lifeline Rescue with AstraDB integration, public pages, admin dashboard, image uploads, and CRUD APIs.

## Setup

1. Create and activate a virtual environment:
   - `python3 -m venv .venv`
   - `source .venv/bin/activate`
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Optional: create `.env` in the project root (or copy from `.env.example`) if you want custom values.
   - The app runs without env vars right now.
   - DB-related vars are only needed when AstraDB is enabled.
   - Optional imgbb vars for hosted image URLs: `IMGBB_API_KEY`, `IMGBB_EXPIRATION`
   - Optional Cloudinary vars for persistent pet/lost+found image URLs: `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_UPLOAD_PRESET`, `CLOUDINARY_UPLOAD_FOLDER`
   - Optional direct Astra image storage vars: `STORE_IMAGES_IN_ASTRA=true`, `ASTRA_INLINE_IMAGE_MAX_BYTES=5600`
   - Optional SMTP vars for adoption/contact email delivery: `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USE_TLS`, `MAIL_USE_SSL`, `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_DEFAULT_SENDER`
   - Optional admin seed vars: `ADMIN_EMAIL`, `ADMIN_PASSWORD`, `ADMIN_FIRST_NAME`, `ADMIN_LAST_NAME`
   - Seeded admins use the temporary password `change-me-now` and must change it on first login.
4. Run:
   - `python run.py`

## Run With Docker

1. Create your env file:
   - `cp .env.example .env`
   - Update values in `.env`.
2. Build and start with Docker Compose:
   - `docker compose up --build`
3. Open:
   - `http://localhost:5000`

### Docker Commands (Without Compose)

1. Build image:
   - `docker build -t boot-hill-lifeline-rescue .`
2. Run container:
   - `docker run --rm -p 5000:5000 --env-file .env -v $(pwd)/app/static/uploads:/app/app/static/uploads boot-hill-lifeline-rescue`

## Deploy To Heroku

1. Login and create app:
   - `heroku login`
   - `heroku create <your-app-name>`
2. Optional config vars (not required for current no-DB phase):
   - `heroku config:set FLASK_SECRET_KEY=<secret> -a <your-app-name>`
   - `heroku config:set PAYMENT_LINK=<donation-url> -a <your-app-name>`
   - `heroku config:set ASTRA_DB_API_ENDPOINT=<endpoint> ASTRA_DB_APPLICATION_TOKEN=<token> ASTRA_DB_KEYSPACE=<keyspace> -a <your-app-name>`
   - `heroku config:set IMGBB_API_KEY=<api-key> IMGBB_EXPIRATION=<seconds-optional> -a <your-app-name>`
   - `heroku config:set CLOUDINARY_CLOUD_NAME=<cloud-name> CLOUDINARY_UPLOAD_PRESET=<unsigned-preset> CLOUDINARY_UPLOAD_FOLDER=bhlr/pets -a <your-app-name>`
   - `heroku config:set MAIL_SERVER=<smtp-host> MAIL_PORT=587 MAIL_USE_TLS=true MAIL_USERNAME=<smtp-user> MAIL_PASSWORD=<smtp-pass> MAIL_DEFAULT_SENDER=<from-email> -a <your-app-name>`
3. Optional admin seed vars:
   - `heroku config:set ADMIN_USERNAME=<username> ADMIN_PASSWORD=<password> -a <your-app-name>`
4. Deploy:
   - `git push heroku main`
   - If your default branch is `master`, use `git push heroku master`.
5. Open the app:
   - `heroku open -a <your-app-name>`

### Bring The Team In

1. Add collaborators:
   - `heroku access:add teammate@example.com -a <your-app-name>`
2. View collaborators:
   - `heroku access -a <your-app-name>`

### Important Heroku Note

- Heroku dyno filesystems are ephemeral. Uploads written to `app/static/uploads` do not persist across dyno restarts or deploys.
- This app can upload images to Cloudinary and store hosted URLs in AstraDB when Cloudinary env vars are set.
- This app can upload images to imgbb and store hosted URLs in AstraDB when `IMGBB_API_KEY` is set.
- This app can also store very small images directly in AstraDB as `data:` URLs when `STORE_IMAGES_IN_ASTRA=true`.
- Astra enforces indexed string limits; large inline images are automatically skipped and fall back to Cloudinary/local upload behavior.
- Without Cloudinary vars, uploads fall back to local `app/static/uploads` storage.

## Routes

### Public Pages
- `/`
- `/about`
- `/adopt`
- `/adopt/<pet_id>`
- `/lostfound`
- `/donate`
- `/volunteer`
- `/tips`
- `/contact`

### Admin Pages
- `/admin/login`
- `/admin`
- `/admin/pets`
- `/admin/lostfound`
- `/admin/content`

### API
- `GET /api/pets`
- `POST /api/pets` (admin)
- `PUT /api/pets/<pet_id>` (admin)
- `DELETE /api/pets/<pet_id>` (admin)
- `GET /api/lostfound`
- `POST /api/lostfound`
- `PUT /api/lostfound/<post_id>` (admin)
- `DELETE /api/lostfound/<post_id>` (admin)
- `GET /api/tips`
- `POST /api/tips` (admin)
- `PUT /api/tips/<tip_id>` (admin)
- `DELETE /api/tips/<tip_id>` (admin)
- `GET /api/content`
- `PUT /api/content` (admin)
- `POST /api/adoption-applications`
- `POST /api/contact-messages`

## Notes
- Uploaded images are saved in `app/static/uploads`.
- Site artwork and shared assets can be stored in `app/static/images`.
- Accepted image types: JPG, JPEG, PNG.
- Site content is loaded from and saved to AstraDB using the `SiteContent` collection.
- The home page Lost & Found preview can be toggled from admin tools.
- Admin users are stored in the `bhlr_admin` collection with fields: `username`, `password_hash`, `first_name`, `last_name`, `email`, `role`, `is_active`, `created_at`, `updated_at`.
- Contact and adoption application forms send server-side email to admin recipients when SMTP env vars are configured.
