# Boot Hill Integrated Deployment Instructions

These instructions apply when deploying the updated integrated Boot Hill Lifeline Rescue app to Heroku.

## Required Deployment Target

- Heroku app: `bhlr`
- Heroku container image: `registry.heroku.com/bhlr/web`
- Production domain: `https://www.boothilllifelinerescue.org`
- Integrated Dockerfile: `boot_hill_lifeline_rescue/Dockerfile.integrated`
- Required build context: the repository root containing both directories:
  - `boot_hill_lifeline_rescue/`
  - `GAssistant/`

## Non-Negotiable Rules

1. Do not deploy the old standalone rescue app.
2. Do not use the inner `boot_hill_lifeline_rescue` directory as Docker build context.
3. Do not modify `GAssistant/` during deployment.
4. Do not modify `.env` or print secrets.
5. Do not run `git push heroku`; this app is deployed through the Heroku container registry.
6. Do not create a new Heroku app.
7. Do not change or remove existing Heroku config vars.
8. Do not run `heroku config:unset`.
9. Do not commit changes or create branches.
10. Never run `cd`, `pushd`, `popd`, or any command that changes the working directory.
11. Assume Copilot is already running from the correct repository root. Execute every command from that starting directory.
12. If a required command fails, stop and report the command and concise error. Do not improvise a different deployment method.

## Expected Repository Layout

The working directory for deployment must contain:

```text
GAssistant/
boot_hill_lifeline_rescue/
```

The integrated Dockerfile must contain the equivalent of:

```dockerfile
COPY boot_hill_lifeline_rescue/requirements.txt /tmp/host-requirements.txt
COPY GAssistant/requirements.txt /tmp/assistant-requirements.txt
COPY boot_hill_lifeline_rescue/ /app/
COPY GAssistant/ /opt/gassistant/
```

If either source directory or the integrated Dockerfile is missing, stop and report the missing path.

## Deployment Procedure

Execute these commands in this exact order from the current working directory. Do not change directories.

## Exact Copy-Paste Commands

Run the following commands exactly as written. The terminal must already be at the repository root containing `GAssistant/` and `boot_hill_lifeline_rescue/`.

```bash
test -d GAssistant && test -d boot_hill_lifeline_rescue && test -f boot_hill_lifeline_rescue/Dockerfile.integrated && test -f boot_hill_lifeline_rescue/Procfile && test -f boot_hill_lifeline_rescue/run.py
```

```bash
heroku container:login
```

```bash
docker buildx build --platform linux/amd64 --provenance=false --sbom=false --file boot_hill_lifeline_rescue/Dockerfile.integrated --output=type=image,name=registry.heroku.com/bhlr/web,push=true,oci-mediatypes=false .
```

```bash
heroku container:release web -a bhlr
```

```bash
curl -I --max-time 30 https://www.boothilllifelinerescue.org
```

```bash
curl --max-time 30 https://www.boothilllifelinerescue.org/assistant/health
```

```bash
curl --max-time 30 https://www.boothilllifelinerescue.org/api/pets
```

If any command fails, stop immediately and report the failed command and its error. Do not continue to the next command.

### 1. Confirm Location

```bash
pwd
```

The output must be the repository root containing both `GAssistant` and `boot_hill_lifeline_rescue`.

### 2. Confirm Required Files

```bash
test -d GAssistant && \
test -d boot_hill_lifeline_rescue && \
test -f boot_hill_lifeline_rescue/Dockerfile.integrated && \
test -f boot_hill_lifeline_rescue/Procfile && \
test -f boot_hill_lifeline_rescue/run.py
```

If any command returns a nonzero exit code, stop.

### 3. Log In To Heroku Container Registry

```bash
heroku container:login
```

If this fails, stop.

### 4. Build And Push Integrated Image

```bash
docker buildx build \
  --platform linux/amd64 \
  --provenance=false \
  --sbom=false \
  --file boot_hill_lifeline_rescue/Dockerfile.integrated \
  --output=type=image,name=registry.heroku.com/bhlr/web,push=true,oci-mediatypes=false \
  .
```

Do not remove `--platform linux/amd64`, `--provenance=false`, `--sbom=false`, or `oci-mediatypes=false`.

### 5. Release The Image

```bash
heroku container:release web -a bhlr
```

Wait for the command to finish. If it fails, stop.

### 6. Verify Production

```bash
curl -I --max-time 30 https://www.boothilllifelinerescue.org
curl --max-time 30 https://www.boothilllifelinerescue.org/assistant/health
curl --max-time 30 https://www.boothilllifelinerescue.org/api/pets
```

Expected results:

- Website request returns HTTP `200`.
- Assistant health returns JSON with `"status":"ok"` when `OPENAI_API_KEY` and assistant configuration are valid.
- Pet API returns JSON.

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
