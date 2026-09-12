# Sana Sana Cafe (DrinkShop) Deployment Instructions

These instructions apply when deploying the Sana Sana Cafe Flask web application to Heroku.

## Deployment Overview & Rules

- **Heroku App Name:** `sana-sana-cafe`
- **Container Registry Target:** `registry.heroku.com/sana-sana-cafe/web`
- **Dockerfile Path:** `./Dockerfile`
- **Build Context:** Workspace root (`.`)
- **App Web URL:** `https://sana-sana-cafe-c6067fd2c0e7.herokuapp.com/`

## Deployment Procedure

Execute these exact steps in order from the repository root:

### 1. Authenticate with Heroku Container Registry

Ensure environment variables from `.env` (including `HEROKU_API_KEY`) are exported if necessary, then log in:

```bash
export $(grep -v '^#' .env | xargs) && heroku container:login
```

### 2. Build and Push Image with Docker Buildx

Build for `linux/amd64` using `buildx` with explicit flags to avoid OCI manifest / attestation issues on Heroku:

```bash
docker buildx build \
  --platform linux/amd64 \
  --provenance=false \
  --sbom=false \
  -t registry.heroku.com/sana-sana-cafe/web:latest \
  --output=type=image,name=registry.heroku.com/sana-sana-cafe/web,push=true,oci-mediatypes=false \
  .
```

### 3. Release Web Container

Release the pushed web image to the `sana-sana-cafe` Heroku app:

```bash
heroku container:release web -a sana-sana-cafe
```

### 4. Verify Health

Verify that the site is active and returning HTTP `200`:

```bash
curl -I --max-time 30 https://sana-sana-cafe-c6067fd2c0e7.herokuapp.com/
```

## Required Integrated Runtime Configuration

The integrated image must run the normal rescue app through `run.py` and must register the assistant only when:

```text
ASSISTANT_ENABLED=true
```

The integrated runtime must use these values:

```text
ASSISTANT_SITE_ID=boot-hill-lifeline-rescue
ASSISTANT_NAME=Boot Hill Rescue Assistant
ASSISTANT_CONTACT_LABEL=contact the Rescue Team
KNOWLEDGE_ROOT=/opt/gassistant/sites/boot-hill-lifeline-rescue/knowledge
PETS_API_URL=http://127.0.0.1:5000/api/pets
PET_PROFILE_URL_TEMPLATE=/adopt/{pet_id}
```

Do not put `OPENAI_API_KEY` or any other secret in this file. Secrets belong in Heroku config vars.

## Existing Heroku Configuration

The existing `bhlr` app already owns the production domain, SSL certificate, Astra DB configuration, Gmail SMTP configuration, imgbb configuration, and admin configuration. Preserve those values.

If the assistant health endpoint reports missing OpenAI configuration, check the variable without printing its value:

```bash
heroku config:get OPENAI_API_KEY -a bhlr | wc -c
```

Only if the length is zero, instruct the user to set the secret directly in their terminal:

```bash
heroku config:set OPENAI_API_KEY=YOUR_OPENAI_KEY -a bhlr
```

Do not ask the user to paste the secret into chat.

## Rollback Guidance

Do not attempt an automatic rollback. If the new release is unhealthy, report the failed endpoint and relevant non-secret Heroku status output, then wait for explicit user direction.

## Final Response Requirements

After a successful deployment, report only:

- Integrated image built and pushed.
- `web` process released to Heroku app `bhlr`.
- Verification results for the production domain, assistant health endpoint, and pet API.
- Any endpoint that did not return the expected result.

Do not claim email delivery, assistant availability, or application behavior succeeded unless the corresponding verification command confirms it.
