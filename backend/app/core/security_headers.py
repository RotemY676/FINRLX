"""Security headers middleware (Phase MVP-5).

Adds defense-in-depth HTTP headers to every response. These don't replace
auth or rate-limiting, but they harden the API against the cheap attacks
that scanners look for (clickjacking, MIME sniffing, downgrade, referrer
leakage).

Notes:
- CSP is intentionally NOT set here because this is a JSON API; a browser
  never renders these responses as a document.
- US-P0-05 correction (2026-07-22): this note previously asserted that "the
  frontend (Next.js) sets its own CSP via next.config.js / meta tags". That
  was not true — the live frontend was measured serving *zero* security
  headers. The claim documented a control that did not exist. The frontend
  now really does set them, in `frontend/next.config.js` (`headers()`);
  if that ever regresses, this comment is wrong again.
- HSTS is only sent over HTTPS — sending it over HTTP is meaningless and
  some browsers warn about it. We add it unconditionally because Railway
  terminates TLS upstream; the browser sees HTTPS.
- The middleware lives in app.core (not app.middleware) for parity with
  the rest of the auth/config code.
"""
from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

_HEADERS: dict[str, str] = {
    # Clickjacking: refuse to be framed.
    "X-Frame-Options": "DENY",
    # MIME-sniffing: trust the declared Content-Type.
    "X-Content-Type-Options": "nosniff",
    # Send no Referer cross-origin (privacy + token leakage prevention).
    "Referrer-Policy": "no-referrer",
    # Force HTTPS for the duration. 1 year + subdomains; preload-eligible.
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    # Disable powerful browser APIs the JSON API does not need.
    "Permissions-Policy": "geolocation=(), microphone=(), camera=(), payment=()",
    # Cross-origin resource sharing isolation hints.
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Resource-Policy": "same-site",
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        for header, value in _HEADERS.items():
            response.headers.setdefault(header, value)
        return response
