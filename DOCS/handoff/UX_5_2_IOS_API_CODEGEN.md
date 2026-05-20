# UX-5.2 — iOS API codegen scaffold

This doc captures the plan for generating Swift `Codable` types + a client from the FastAPI backend's OpenAPI spec. **No Swift project exists yet** — this is the brief for the iOS dev who picks up Phase D (currently deferred per the PWA-first decision in UX/UI track scope).

## OpenAPI source

The FastAPI backend exposes its full spec at runtime:

```
GET http://127.0.0.1:8000/openapi.json
GET https://backend-production-aab8.up.railway.app/openapi.json   # prod
```

Every route in `backend/app/api/v1/*.py` is auto-included with its Pydantic request/response types as the `components.schemas`. No manual schema curation is required.

## Recommended tool

[swift-openapi-generator](https://github.com/apple/swift-openapi-generator) — Apple-official, ships through Swift Package Manager, generates `Sendable` `Codable` types + an async/await client.

Alternatives considered + rejected for this project:
- `openapi-codegen` (CocoaPods) — old, no async/await support
- Hand-rolled types — drifts the moment a backend dev adds a field

## Project layout (when iOS work starts)

```
ios/
└── finrlx/
    ├── Package.swift
    ├── openapi.yaml                              # snapshot of /openapi.json
    ├── openapi-generator-config.yaml             # generator settings
    └── Sources/
        ├── FinrlxAPI/                            # generated, do not edit
        │   ├── Client.swift
        │   ├── Types.swift
        │   └── Operations.swift
        └── Finrlx/                               # hand-written app code
            └── ...
```

`openapi.yaml` is committed (snapshot). A `make sync-api` target in the iOS project should fetch the latest from the prod backend, diff against the snapshot, and only update on a deliberate dev action. This stops a backend hotfix from invisibly mutating the iOS client.

## Generator config

```yaml
# openapi-generator-config.yaml
generate:
  - types
  - client
namingStrategy: idiomatic
accessModifier: public
filter:
  paths:
    - /api/v1/overview
    - /api/v1/recommendations/current
    - /api/v1/decision/stages
    - /api/v1/comparison/current
    - /api/v1/replay
    - /api/v1/replay/{recommendation_id}
    - /api/v1/backtests
    - /api/v1/backtests/{backtest_id}
    - /api/v1/paper/current
    - /api/v1/paper/{portfolio_id}/drift
    - /api/v1/universes
    - /api/v1/universes/{universe_id}
    - /api/v1/universes/{universe_id}/coverage
    - /api/v1/universes/{universe_id}/readiness
    - /api/v1/flags
    - /healthz
```

The path filter omits admin / RL / training endpoints from the iOS bundle — they're desktop-only per UX-2.6. The iOS app should never need them.

## SwiftPM dependency

```swift
// Package.swift
.package(url: "https://github.com/apple/swift-openapi-generator", from: "1.0.0"),
.package(url: "https://github.com/apple/swift-openapi-runtime", from: "1.0.0"),
.package(url: "https://github.com/apple/swift-openapi-urlsession", from: "1.0.0"),
```

## Authentication

FastAPI MVP-1 wires JWT access tokens in `Authorization: Bearer …` headers. The iOS client should set this via a `ClientMiddleware`:

```swift
struct AuthMiddleware: ClientMiddleware {
  let tokenProvider: () async throws -> String
  func intercept(...) async throws -> ... {
    var req = request
    let token = try await tokenProvider()
    req.headerFields[.authorization] = "Bearer \(token)"
    return try await next(req, body, baseURL)
  }
}
```

`tokenProvider` reads from Keychain. Refresh-token rotation handled by a separate `AuthManager` actor.

## Contract testing

When the iOS project lands, add:
- A Swift Testing test that calls a small subset of endpoints against a recorded fixture (no live backend in CI).
- A backend-side test in `backend/tests/` that confirms `/openapi.json` is reachable + has the right shape (so a backend refactor that breaks the spec fails CI before the iOS app sees it).

## Until then

No code to ship in this sub-phase. The doc above + the locked iOS-bridging decisions in `UX_TRACK.md` UX-5 are the deliverable. When Phase D opens, the iOS dev reads this and follows the recipe.
