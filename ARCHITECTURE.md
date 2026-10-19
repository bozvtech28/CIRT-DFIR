# CIRT-DFIR Architecture

**Status:** Current implementation and target-state reference  
**Repository:** [bozvtech28/CIRT-DFIR](https://github.com/bozvtech28/CIRT-DFIR)  
**Baseline reviewed:** `f6b272046f2d94712e0f5f8ed32a1e4ddfcb76b6` on `main`  
**Last reviewed:** 2026-10-19

> This document distinguishes what is present in the repository from what is proposed or still gated. The repository is a development workspace; it must not be treated as a production DFIR service. Entra/OIDC building blocks and configuration plans exist, but the FastAPI authentication dependency remains fail-closed and does not invoke them.

## 1. Purpose and scope

CIRT-DFIR is being developed as a modular computer incident response and digital forensics platform. Its intended lifecycle includes case and asset management, authorized endpoint triage, evidence intake and custody, analyst findings, controlled response actions, reporting, and post-incident review.

The initial production target documented by the project is authorized Windows endpoint triage and evidence handling. Additional operating systems and mobile acquisition require separately validated modules and must not be implied by the current prototype.

### Current maturity

| Area | Observed state in `main` |
|---|---|
| React web application | Development scaffold with navigation, case register, local filtering, read-only detail view, and synthetic-data messaging |
| Static HTML prototype | Separate offline UI prototype at `apps/web-prototype/index.html`; fictional records only |
| FastAPI | Development API scaffold with health, synthetic case list, and case update routes |
| Case persistence | SQLite repository/schema and synthetic case seeding |
| Audit events | Case create/update events are written with case records; schema prevents ordinary UPDATE/DELETE, but not direct database-file tampering |
| Authorization policy | Role/permission module exists, but request identity acquisition always returns HTTP 401 |
| Entra/OIDC | Offline-verification, metadata/JWKS and role-mapping components plus synthetic tests exist; intentionally not wired into FastAPI pending approved configuration and security sign-off |
| Evidence intake/storage | Not implemented as an operational flow |
| Endpoint scanner | Intended as a separately packaged and signed application; not integrated into the running platform |
| Production readiness | Not established; security and acceptance gates remain open |

## 2. System context and boundaries

The repository contains multiple related but distinct deliverables:

1. **Current web platform scaffold** — React + TypeScript application built with Vite, backed in development by a FastAPI service.
2. **Offline web prototype** — standalone HTML/CSS/JavaScript mock-up for reviewing broad workspace layout; it has no live API or authentication integration.
3. **Backend identity foundations** — isolated Entra/OIDC token-verification primitives and test harnesses. Their presence is not proof the application currently authenticates users.
4. **Future endpoint scanner and evidence workflow** — target capabilities in `docs/Architecture.md` and `docs/Requirements.md`, not operational integrations.

### Current development request flow

```text
Browser (React / TypeScript)
  ├─ AuthRoot / MSAL configuration and session controls
  └─ App (case list, filters, detail view)
       |
       | authenticatedFetch: acquires access token, adds Bearer header
       v
Vite dev server (127.0.0.1; /api proxy)
       |
       v
FastAPI (127.0.0.1:8000 in development)
  ├─ GET  /api/v1/health
  ├─ GET  /api/v1/demo/cases  ── require_permission("cases:read")
  └─ PATCH /api/v1/cases/{case_id} ── require_permission("cases:update")
       |
       v
Authentication dependency (currently fail-closed: HTTP 401)
       |
       └─ Protected routes do not currently reach their case business logic
```

When the frontend cannot reach the local API because of a network failure, it can present a clearly labelled local synthetic fallback. HTTP errors, including authentication/authorization errors, do not fall back to the synthetic list. Browser state and tokens are not an authorization source for the server.

## 3. Repository map

Paths below identify active/documented source areas. Timestamped backups, checked-in virtual environments, and frontend `node_modules` exist in the repository but are not runtime architecture modules.

| Path | Responsibility |
|---|---|
| `README.md` | Workspace overview, prototype constraints, security warning and Entra configuration guidance |
| `docs/Architecture.md` | Earlier proposed/target platform architecture and ingestion security requirements |
| `docs/Requirements.md` | Functional, security, evidence, usability and acceptance requirements |
| `docs/ENTRA_AUTH_INTEGRATION_DESIGN.md` | Entra trust flow and activation gates |
| `docs/ENTRA_ADMIN_CONFIGURATION_REQUEST.txt` | Placeholder worksheet for approved identity configuration |
| `docs/Phase8B*.md` and related text files | Phase-by-phase design, readiness, configuration and test records; not deployment approval |
| `UI_UX.md` | Universal UX, accessibility and interface-quality standard |
| `apps/web-prototype/index.html` | Independent static offline mock-up with fictional content |
| `platform/frontend/index.html` | Vite HTML entry point |
| `platform/frontend/src/main.tsx` | React root; mounts `AuthRoot` |
| `platform/frontend/src/App.tsx` | Navigation, synthetic case list, filters, refresh and read-only detail |
| `platform/frontend/src/style.css` | Responsive dark-theme styling and page/component presentation |
| `platform/frontend/src/auth/AuthRoot.tsx` | Authentication status, MSAL initialization, sign-in/sign-out controls |
| `platform/frontend/src/auth/entraConfig.ts` | Reads SPA configuration from Vite variables and validates placeholders/URI |
| `platform/frontend/src/auth/msalInstance.ts` | Creates/initializes MSAL client and processes redirects |
| `platform/frontend/src/auth/entraToken.ts` | Silently acquires an API token for the selected account |
| `platform/frontend/src/auth/authenticatedFetch.ts` | Attaches access token in Authorization Bearer header |
| `platform/backend/app/main.py` | FastAPI app, models and API routes |
| `platform/backend/app/auth_dependencies.py` | Route permission dependency; currently rejects protected requests while auth is unconfigured |
| `platform/backend/app/security.py` | Internal roles, permission mapping, principal shape, validation and RBAC |
| `platform/backend/app/entra_*.py`, `oidc_claims.py` | Isolated Entra/OIDC token, claim, metadata, transport, JWKS/cache, preflight and principal mapping |
| `platform/backend/app/case_store.py` | SQLite path, initialization and synthetic seeding |
| `platform/backend/app/case_repository.py` | SQLite connection, case helpers and audit-event persistence |
| `platform/backend/app/case_schema.sql` | Case/audit schema, indexes, constraints and append-only triggers |
| `platform/backend/data/cirt_cases.sqlite` | Checked-in SQLite development data; not production storage |
| `platform/backend/tests/` | API, fail-closed auth, token verification, metadata/JWKS, claims, roles and security tests |
| `platform/backend/synthetic_test_support/` | Synthetic JWT/RS256 helpers and synthetic role mapping |
| `platform/backend/requirements.txt` | Backend dependency declarations |
| `platform/frontend/package.json`, `package-lock.json` | Frontend scripts, dependencies and lockfile |
| `platform/frontend/vite.config.ts` | Local Vite server and `/api` proxy to localhost port 8000 |
| `.env.example` | Non-secret placeholder names for backend Entra settings |
| `.gitignore` | Ignores `.env` and `.env.*`, while retaining `.env.example` |
| `Reports/Baseline_Report_20261015_223611.txt` and inventory CSV | Historical inventory and recorded filesystem-containment gate |

## 4. Frontend architecture

### Stack and startup

The active frontend uses React 19, TypeScript, Vite, MSAL Browser and MSAL React. The package build script runs TypeScript project builds followed by `vite build`. Vite is configured to bind to `127.0.0.1`, use a strict port, and proxy `/api` to `http://127.0.0.1:8000` for local development.

### Responsibilities and state

- `main.tsx` mounts the app in React Strict Mode and loads the stylesheet.
- `AuthRoot` checks configuration, initializes MSAL, handles redirects and presents sign-in state. With missing/placeholder settings it explicitly says authentication is not configured but still renders the development application.
- `App` requests `/api/v1/demo/cases`, checks the basic response shape, and displays API/network errors, synthetic fallback, search/filter options and read-only details.
- Navigation items other than Dashboard/Cases are scaffold placeholders rather than completed workflows.
- The frontend labels its case data as synthetic and explicitly states the product is not operational.

The frontend is not the authorization boundary. Even successful MSAL sign-in does not unlock protected API routes while the backend dependency remains fail-closed. Do not change that dependency to accept identity or role data from the browser.

## 5. Backend and API architecture

### Runtime and dependencies

The API uses Python, FastAPI and Pydantic. Declared dependencies include Uvicorn, pytest, HTTPX, PyJWT and cryptography. The API identifies itself as version `0.1.0` and labels its mode `development-scaffold`.

### Current endpoints

| Endpoint | Current purpose | Access behavior |
|---|---|---|
| `GET /api/v1/health` | Returns simple health/mode response | Public; returns development-scaffold mode |
| `GET /api/v1/demo/cases` | Returns synthetic case register from SQLite store | Requires `cases:read`; currently rejected with HTTP 401 |
| `PATCH /api/v1/cases/{case_id}` | Updates case status and/or severity; attributes the event to principal subject | Requires `cases:update`; currently rejected with HTTP 401 before update logic |

The PATCH model forbids extra request fields and requires status, severity or both. The repository restricts status/severity to known values, rejects missing cases and no-op changes, and writes the update and audit event transactionally. These business functions exist in source, but the full HTTP workflow is not operational while the authentication dependency rejects every request.

### Storage model

SQLite is the current development persistence implementation. `CIRT_DFIR_DB_PATH` can override the default path; otherwise it resolves to `platform/backend/data/cirt_cases.sqlite`.

The schema contains:
- `cases`: ID, title, severity, status, creation/update timestamps, creator and version.
- `audit_events`: case reference, event type, actor, event time, JSON details and optional previous/event hashes.

Foreign keys and severity/status checks are enabled; ordinary audit-event UPDATE and DELETE statements are rejected by triggers. This is a local integrity guard, not a verified tamper-proof ledger: hash fields exist, but repository logic does not establish complete chain verification or protect against an administrator directly editing the database file. SQLite is not the proposed production PostgreSQL database.

## 6. Authentication and authorization

### Frontend pieces

The SPA reads `VITE_ENTRA_TENANT_ID`, `VITE_ENTRA_CLIENT_ID`, `VITE_ENTRA_API_SCOPE` and `VITE_ENTRA_REDIRECT_URI`. It validates missing/placeholders, checks GUID shape for tenant/client and requires HTTPS redirect URIs except localhost development. MSAL cache is set to session storage; API requests carry a silently acquired access token.

### Backend pieces and current gate

The backend has:
- a `Principal(subject, roles)` model;
- Administrator, DFIR Analyst and Viewer roles;
- permission mappings including `cases:read` and `cases:update`;
- isolated bearer parsing, JWT verification, approved-claim-to-role mapping, metadata checks, allowlisted JWKS fetch/cache, timeouts and response-size limits;
- offline unit/integration tests for these components.

However, `platform/backend/app/auth_dependencies.py:get_current_principal()` always raises HTTP 401 with an “Authentication is not configured” response. The Entra authenticator and bearer adapter explicitly state they are not wired into FastAPI. Current app-level authentication is **not active**; the live API dependency cannot produce the principal needed by route authorization.

### Activation gate

Do not activate the adapter until the approved tenant ID, exact issuer, API audience, discovery/JWKS host allowlists, SPA client ID, API scope, redirect URI, Entra role values and internal role mapping are supplied/approved by authorized identity/security owners. Then wire the verified principal into the dependency, preserve server-side route authorization, verify audit attribution, run the complete local backend suite and frontend build, review a real-token configuration, and obtain formal security/application-owner approval. Synthetic token tests do not prove production identity.

## 7. Case data and audit events

The repository initializes SQLite only when the configured database is missing or empty and seeds three fixed `DEMO-2026-*` cases only when there are no case rows. This is development seeding, not a production migration strategy.

Case updates are designed to validate status/severity against allowlists, load the existing case, reject missing/no-op updates, capture before/after values, commit the update and audit event together, and attribute the action to the authenticated principal's subject. End-to-end attribution is not currently active because the API dependency rejects requests before creating a principal.

## 8. Target-state architecture (proposed, not implemented)

The earlier architecture proposal describes a modular platform consisting of:

- **DFIR web platform:** UI, API, case/workflow services, evidence intake, findings and reporting.
- **Endpoint scanner:** separately packaged and signed Windows application, with enrolled endpoint identity and short-lived revocable credentials.
- **Metadata database:** PostgreSQL as proposed production storage.
- **Evidence object storage:** S3-compatible storage such as MinIO, separated from searchable case metadata.
- **Optional job queue:** Redis + Celery for asynchronous workloads.
- **Deployment:** Docker Compose for server services; signed scanner installer on endpoints.
- **Modes:** offline local operation with controlled import/export, intranet deployment over HTTPS/restricted subnets, and hosted deployment with TLS, MFA, private management access, monitoring, retention and disaster recovery.

These are target design choices from `docs/Architecture.md`, not current dependencies or operational deployments. Do not claim PostgreSQL, object storage, queues, scanner enrollment, evidence ingestion, containers or response execution are active until implemented and verified.

### Intended future evidence flow

1. An authorized operator selects a case, collection profile and scope.
2. Policy checks present scope, exclusions, privilege needs and expected impact before collection.
3. A signed scanner collects authorized artifacts and emits a manifest with version, source context, scope, timestamps, sizes and SHA-256 hashes.
4. A bounded authenticated ingest flow stages the package privately, validates paths/quotas, computes hashes server-side and atomically finalizes it.
5. Received originals are preserved; searchable metadata remains separate from evidence blobs.
6. Custody/access events and derived artifacts retain provenance; hashes help integrity verification but do not alone prove authenticity or completeness.
7. Analysts record findings/dispositions; disruptive response actions require policy checks, explicit approval and audit records.
8. Reports summarize case state, evidence registers, collection limitations and custody history.

This is requirements-derived target behavior, not the current implementation.

## 9. Security and trust boundaries

Treat future evidence, API requests, endpoint reports and import packages as untrusted until validated.

- **Browser to API:** browser claims/roles are untrusted; validate API tokens server-side and authorize every protected operation.
- **Identity provider to API:** use approved issuer/audience/tenant and trusted HTTPS discovery/JWKS hosts; reject invalid metadata or unknown/untrusted keys and never follow token-supplied URLs.
- **API to database:** use parameterized queries, schema constraints, transactions, least-privilege access, protected backups and restore tests.
- **Evidence package to staging:** use bounded streaming, request deadlines, byte/member quotas, private staging, strict path validation, defenses against traversal/junctions/reparse points and concurrent path changes, exclusive creation and explicit cleanup ownership.
- **Original and derived evidence:** preserve originals, identify transformed artifacts, retain provenance/custody, verify hashes at ingest and after storage, and restrict deletion/retention changes.
- **Response actions:** no disruptive operation is implemented in the current scaffold; target actions require policy authorization, explicit approval, scope validation and auditable outcomes.
- **Configuration/secrets:** keep real environment files, credentials, access tokens and private keys out of source control and logs. Examples and worksheets are placeholders only.
- **Operations:** require HTTPS for intranet/hosted deployment, origin/CORS allowlists, monitoring, retention, tested backups/restoration, dependency management, SBOM and signed release artifacts before use.

## 10. Known gaps and release gates

1. **P1 filesystem containment: OPEN.** The baseline report records that a native review prototype accepted a path through a parent junction in a synthetic test. Do not integrate it as a fix or begin production evidence integration until an independently reviewed correction covers traversal, junctions/reparse points, races, cleanup ownership and safe finalization.
2. **Authentication: NOT ACTIVE.** Protected backend routes return HTTP 401 while the fail-closed dependency is in place. Entra integration awaits approved configuration and adapter wiring.
3. **Production evidence pipeline: ABSENT.** No verified production ingest, object store, custody service, scanner connection or response execution flow exists.
4. **Storage migration/operations: NOT COMPLETE.** SQLite is the development data store; production PostgreSQL/object-store design, migrations, encryption, backup and restoration remain unestablished.
5. **UI routes: PARTIAL.** Dashboard/Cases have a synthetic read-only list/detail flow; other navigation modules are scaffold placeholders.
6. **Workspace hygiene: REVIEW REQUIRED.** The tracked tree includes dependency directories, virtual-environment trees and timestamped backups. This document does not remove them; confirm references and repository policy before cleanup.
7. **Live deployment: NOT VERIFIED.** Source and tests are not evidence that production infrastructure, live identity configuration or Windows endpoint workflows work.

### Minimum acceptance gate before production

- Independently remediate and acceptance-test the P1 filesystem-containment issue.
- Complete verified live OIDC integration with approved settings, negative-token and role tests, and principal-derived audit attribution.
- Enforce case/object-level authorization on every protected operation.
- Pass bounded-upload and filesystem tests covering traversal, junctions, races, partial uploads, cleanup and preservation of pre-existing files.
- Verify evidence hashes, provenance/custody and safe original/derived artifact handling.
- Validate production database/object store, encryption, backups and restoration.
- Demonstrate offline/intranet deployment, monitoring, dependency/SBOM/release-signing controls.
- Pass local non-CI tests and frontend production build, security review, and explicit CIRT/application-owner approval.

## 11. Local development and validation entry points

Commands are based on checked-in package/test configuration; successful execution is not implied by this document.

### Backend

From `platform/backend`, install `requirements.txt` dependencies and run:

```powershell
python -m pytest
```

The app import path is `app.main:app`. A development server can be started using Uvicorn, but keep it on a local-only development environment. Protected endpoints currently fail closed; do not weaken that gate to enable a demo.

### Frontend

From `platform/frontend`:

```powershell
npm ci
npm run build
npm run dev
```

The development server proxies `/api` to `127.0.0.1:8000`. Only approved, non-secret SPA configuration should be supplied in local environment variables; never put a client secret in a `VITE_*` variable.

### Static prototype

Open `apps/web-prototype/index.html` directly in a modern browser for offline layout review. It uses fictional content and has no backend, authentication, evidence storage or live response capability.

Run tests/builds locally when dependencies and environment are available. Do not use hosted CI as validation, and do not treat CI status as evidence of correctness.

## 12. Architectural decision principles

- Keep current implementation and future architecture explicitly separated.
- Preserve fail-closed authentication until the approved identity adapter is wired and independently tested.
- Make the backend authoritative for identity, permissions and case/object-level access.
- Preserve original evidence and distinguish acquisition provenance/custody from derived analysis.
- Keep acquisition, ingestion, storage and response boundaries modular rather than embedding endpoint-specific behavior in the web API.
- Gate destructive/disruptive actions with approval and audit records.
- Document only verified deployment/runtime capabilities; synthetic or offline tests do not imply production readiness.
- Update this document when implementation, API contracts, trust boundaries, persistence or deployment topology materially changes.

## 13. Source documents

- [README.md](README.md)
- [Proposed platform architecture](docs/Architecture.md)
- [Initial functional and security requirements](docs/Requirements.md)
- [Entra integration design](docs/ENTRA_AUTH_INTEGRATION_DESIGN.md)
- [Entra administrator configuration request](docs/ENTRA_ADMIN_CONFIGURATION_REQUEST.txt)
- [UI/UX standard](UI_UX.md)
- [Baseline security/inventory report](Reports/Baseline_Report_20261015_223611.txt)
