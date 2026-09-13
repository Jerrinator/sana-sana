# Sana Sana Cafe (DrinkShop) Deployment Instructions

These instructions apply when deploying the Sana Sana Cafe Flask web application to Heroku.

## Border Tile Assets

Decorative talavera-style border/background tiles live in `app/static/images/border_tiles/`:

- `border_design_tile1.png` — a floral picture-frame tile (cream lattice/flower motif on terracotta). It is a full frame design but is also repeatable/tileable, so it can be used as its own repeating border in addition to being combined with other tiles.
- `border_design_tile2.png` — a flower medallion tile (cream 8-petal ring around a forest-green center dot on terracotta), meant as the **preferred** tile for building borders.
- `border_design_tile3.png` — the site's frog mascot, repurposed as a border tile. Its background is intentionally transparent (lets the header bar's cream background show through) — do not fill or flatten this transparency.

Treat these like floor tiles: they can be combined in patterns (alternating, checkerboard, etc.) rather than only used individually. `border_pattern_strip.png` in the same folder is a generated composite laid out as a 2-column x 3-row repeat unit (24x24px cells at 1x, saved at 2x for retina, 48x72px total): the left column is `tile2` in all three rows, and the right column is `tile2` on top and bottom with `tile3` (frog) in the middle — mirroring the original `bordertile_3row.png` layout (dark tile border top/bottom, frog alternating in the middle row). This is what `.artesania-header-bar` in `app/static/css/style.css` uses for the top-of-page border. Regenerate this strip (or create new composites) with Pillow if the tiles or pattern change — do not hand-edit the composite PNG directly, and preserve tile3's transparency when doing so.

The shared card rule (`.hero-copy, .hero-card, .card, .info-block, .stacked-form, .modal-content`) in `app/static/css/style.css` uses `tile1` directly as a CSS `border-image`: `border-image-slice: 300` crops just tile1's own outer decorative band (its center is plain terracotta and is discarded, not stretched with `fill`), giving every card site-wide a thin talavera-patterned frame.

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

## Maintenance Mode

The `SITE_ENABLED` env var (`.env` locally, Heroku config var in production) toggles the whole site:

- `SITE_ENABLED=true` (default) — site behaves normally.
- `SITE_ENABLED=false` — every route except `/static/*` returns the `public/unavailable.html` maintenance page with HTTP `503`, regardless of database or other backend state.

This is enforced by a `before_request` hook in `app/__init__.py`. Toggle it in production with `heroku config:set SITE_ENABLED=false -a sana-sana-cafe` and restore with `SITE_ENABLED=true`.

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
