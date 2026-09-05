# Changes made in this pass

## Integration fixes (backend)

1. **Mappls auth was targeting a dead/wrong flow.**
   Mappls migrated to a static API-key model in August 2025 (the key
   is sent as an `access_token` query parameter on every request,
   replacing OAuth2 client_credentials for most REST endpoints). The
   old code was posting to `outpost.mapmyindia.com` (wrong domain) and
   sending `Authorization: Token <token>` (wrong header). Rewrote
   `backend/app/services/mappls.py` to use your `MAPPLS_API_KEY`
   directly, with the legacy OAuth2 flow kept only as a fallback for
   older Mappls accounts. Also corrected the routing/geocoding
   endpoint URLs to match Mappls' current documented paths
   (`route.mappls.com/route/direction/route_adv/...`).

   Note: Mappls does not expose a simple "traffic incidents in a
   bounding box" REST endpoint on standard plans - `get_traffic()` now
   degrades gracefully (returns an empty incident list + logs a
   warning) instead of crashing the dashboard if that add-on isn't on
   your plan. Traffic-aware ETAs still come through on `get_route()`.

2. **The backend would not have booted.** `security/jwt.py` imports
   `jwt` (the PyJWT package's import name) but `requirements.txt` only
   listed `python-jose` (import name `jose`) - a different package
   entirely. Swapped `python-jose[cryptography]` for `PyJWT==2.9.0`.

3. **Firebase push alerts used a dead Google endpoint.** The legacy
   `fcm.googleapis.com/fcm/send` + server-key API was shut down by
   Google in mid-2024. Rewrote `services/firebase.py` to use the
   current FCM HTTP v1 API via `firebase-admin` (already a listed
   dependency, previously unused). It initializes from
   `FIREBASE_CREDENTIALS_PATH` and no-ops safely until you add a
   service account JSON.

4. **Local dev rate limiting.** `REDIS_URL` now defaults to
   `memory://` in `backend/.env` so SlowAPI's rate limiter works
   without a local Redis instance running. Switch back to a real
   `redis://` URL for production.

5. Wired your real credentials into `backend/.env` / `frontend/.env.local`
   (MongoDB Atlas URI, Mappls API key) and generated fresh
   `SECRET_KEY` / `CSRF_SECRET` values.

## Frontend fix

6. **Every page's `<h1>` was invisible as a heading.** Tailwind's
   preflight reset strips default font-size/weight from `<h1>`-`<h6>`,
   and none of the 9 pages passed a `className` to their `<h1>`. That
   means every page title rendered at the same size/weight as body
   text - a likely source of the "looks unfinished" feel. Fixed with
   three rules added to `index.css` only (no page components touched):
   a global `h1` style, spacing between `h1` and the following `<p>`,
   and a default link style for any future unstyled in-copy links.

## Not changed / needs your attention

- **Mappls `client_id` and `client_secret` you provided are identical
  strings.** That's unusual for a real OAuth key pair. It doesn't
  block anything (the static `MAPPLS_API_KEY` path is now primary and
  ignores both), but double-check them in the Mappls console if you
  ever need the legacy OAuth fallback.
- **Rotate the Mappls key and Mongo password** you shared in this
  chat once you're done testing, since they've now been typed into a
  conversation transcript. Not urgent, just good hygiene.
- I do not have network access in this sandbox, so I could not run
  `pip install` / `npm install` or make live calls to Mappls/MongoDB.
  Every file here passed a Python syntax compile and a CSS brace
  check, and the logic was checked line-by-line against current
  Mappls documentation, but you'll want to actually boot both servers
  locally and click through the app before treating this as final.
- The "Emergency Vehicle HUD" and "Traffic Control" pages are
  currently data tables with no live map view. Given the "don't
  change much frontend" instruction I left this as-is rather than
  introducing a mapping library - flag if you'd like a Mappls Web Maps
  JS view added on top of the existing layout.
