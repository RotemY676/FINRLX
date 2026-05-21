# Google OAuth (Sign in with Gmail) — Setup Runbook

**Date:** 2026-05-21
**Status:** Backend + frontend code shipped. **Blocked on you provisioning
a Google Cloud OAuth client and setting 3 env vars.** Until then,
`/api/v1/auth/google/start` returns `503 Service Unavailable` and the
"Sign in with Google" button on `/login` + `/signup` will render a 503
when clicked.

## What ships in this commit

| Artifact | Path |
|---|---|
| OAuth service | `backend/app/services/google_oauth.py` |
| Endpoints | `backend/app/api/v1/auth.py` — `GET /auth/google/start`, `GET /auth/google/callback` |
| Settings | `backend/app/core/config.py` — `google_oauth_client_id`, `_secret`, `_redirect_uri`, `_post_login_redirect` |
| Frontend buttons | `frontend/src/app/login/page.tsx`, `frontend/src/app/signup/page.tsx` |
| FE finish page | `frontend/src/app/login/google-finish/page.tsx` |
| Tests (6) | `backend/tests/test_phase_oauth_google.py` |

## Security design (audit notes)

* **CSRF protection** via `state` parameter: backend generates 32-byte
  random token, stores in HttpOnly cookie + sends to Google, callback
  verifies cookie value matches the returned state. Cookie is `SameSite=Lax`,
  `Secure` outside `debug` mode, max-age 10 minutes.
* **ID token verified** against Google's JWKS endpoint
  (`https://www.googleapis.com/oauth2/v3/certs`) with RS256, audience
  match, issuer match (`accounts.google.com` family), and `exp/iat/iss/aud/sub`
  required claims. PyJWT does the heavy lifting; we don't trust any field
  not validated by signature.
* **`email_verified` must be `true`** in the ID token — Google only sets
  this on emails they've confirmed the user controls. Refusing
  unverified addresses blocks the historical attack of claiming a
  Gmail address you don't own via SAML/Workspace edge cases.
* **Allowlist enforcement preserved**: a Gmail address not in
  `email_allowlist` cannot complete sign-in, exactly the same gate
  password sign-up uses. The redirect surfaces `?error=not_allowlisted`
  to the FE.
* **Tokens delivered via URL fragment**, not query string — fragments
  never reach the server's access log. The `/login/google-finish`
  page reads them, persists via `setAccessToken/setRefreshToken`, then
  uses `window.history.replaceState` to scrub the URL so a refresh /
  copy-paste of the URL doesn't leak the access token.
* **No long-lived Google refresh token requested**: `access_type=online`
  in the authorization URL. We only need a one-shot identity proof;
  the FINRLX session is our own JWT + refresh, not Google's.
* **Password column still required** on the User row. Google sign-ups
  get a `secrets.token_urlsafe(48)` placeholder password hash so the
  user has no usable password until they explicitly set one (future
  enhancement). Matters because the column is `NOT NULL`.

## You must do this (operator setup)

### 1. Create Google Cloud project

* Open https://console.cloud.google.com → New Project → name "FINRLX".

### 2. Enable the OAuth consent screen

* APIs & Services → OAuth consent screen.
* User Type: **External**.
* App name: FINRLX
* User support email: your email
* Developer contact email: your email
* Scopes: leave default (we only request `openid email profile`).
* Test users: add **all beta-tester Gmail addresses** here (Google
  blocks all other users in test mode).

### 3. Create OAuth Client ID

* APIs & Services → Credentials → Create Credentials → OAuth Client ID.
* Application type: **Web application**.
* Name: "FINRLX backend".
* **Authorized JavaScript origins**:
  - `https://<your-frontend>.up.railway.app`
  - `http://localhost:3000` (for local dev)
* **Authorized redirect URIs**:
  - `https://<your-backend>.up.railway.app/api/v1/auth/google/callback`
  - `http://localhost:8000/api/v1/auth/google/callback`
* Click Create. Copy the **Client ID** and **Client Secret**.

### 4. Paste into Railway env vars (backend service)

```
GOOGLE_OAUTH_CLIENT_ID=<paste here, ends in .apps.googleusercontent.com>
GOOGLE_OAUTH_CLIENT_SECRET=<paste here>
GOOGLE_OAUTH_REDIRECT_URI=https://<your-backend>.up.railway.app/api/v1/auth/google/callback
GOOGLE_OAUTH_POST_LOGIN_REDIRECT=https://<your-frontend>.up.railway.app/login/google-finish
```

For local dev, set the same in `.env` (skip the `.up.railway.app` URLs,
use localhost).

### 5. Verify

```bash
curl -i "$BACKEND/api/v1/auth/google/start"
```

Expected: `HTTP/1.1 302 Found` with `Location` starting with
`https://accounts.google.com/o/oauth2/v2/auth?...`.

If you get 503, the env vars aren't loaded yet — redeploy.

### 6. Smoke the full flow

Open `https://<frontend>.up.railway.app/login` in a browser. Click
"Sign in with Google". You should:

1. Bounce to Google's account picker.
2. Pick a Gmail address that's already in `email_allowlist`.
3. Bounce back to `https://<frontend>.../login/google-finish#access_token=…`.
4. Land on `/` (the home page) signed in.

If the Gmail isn't allowlisted, you see "Complete the wizard first…"
(actually `error=not_allowlisted` — message is rendered verbatim).

### 7. Going to "Production" mode

The OAuth consent screen starts in "Test mode" — only emails listed under
"Test users" can sign in. Once you're ready to open the beta wider:

* OAuth consent screen → Publish App.
* Google will ask for verification if you request sensitive scopes; we
  only request `openid email profile` (none sensitive), so this is a
  click-through. No app-review delay for our scope set.

## Tests shipped

| Test | What it asserts |
|---|---|
| `test_google_start_503_when_unconfigured` | Empty `client_id` → endpoint returns 503 |
| `test_google_start_redirects_with_state_cookie` | Endpoint emits 302 + state cookie set |
| `test_google_callback_state_mismatch` | Wrong state in callback → bounce to FE with `error=state mismatch` |
| `test_google_callback_blocks_non_allowlisted` | Verified Google email but not in allowlist → `error=not_allowlisted` |
| `test_google_callback_blocks_unverified_email` | `verify_id_token` raises → `error=verification:…` |
| `test_google_callback_issues_tokens_for_allowlisted` | Happy path → 302 with `access_token` + `refresh_token` in fragment, `user_email` in fragment |

## Honest limitations

* **The 6 tests stub Google's HTTP layer + JWKS** via monkeypatch. They
  never hit the real Google. The actual signature-verification code in
  `verify_id_token` is exercised only against the real provider, so the
  first live click is the real first integration test. The runbook's
  step 6 covers that.
* **No PKCE on the FE button** — we use the classic confirmation_code
  flow with the secret on the server. PKCE is for SPAs that can't hold
  a secret; we're a server-rendered Next app + a FastAPI backend, so
  the secret stays where it's safe.
* **Account linking semantics**: if a Gmail user with email
  `me@gmail.com` already has a password account with the same email,
  the Google sign-in finds that account and reuses it. There's no
  separate "linked Google account" record yet — the email is the only
  identifier. Acceptable for the closed beta; documented here for
  future hardening.
* **The `email_allowlist` is still the gating mechanism.** Removing it
  would let anyone with a Google account sign up. Don't loosen this
  until you've decided the beta is open.

## Sources

* [Google OAuth 2.0 docs](https://developers.google.com/identity/protocols/oauth2/openid-connect)
* [Google OpenID Connect endpoints](https://accounts.google.com/.well-known/openid-configuration)
* [JWKS endpoint](https://www.googleapis.com/oauth2/v3/certs)
* [OAuth 2.0 RFC 6749 — Authorization Code flow](https://datatracker.ietf.org/doc/html/rfc6749#section-4.1)
