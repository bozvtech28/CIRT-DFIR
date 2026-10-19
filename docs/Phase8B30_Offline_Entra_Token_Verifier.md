# Phase 8B.30 — Offline Entra Token Verifier

## Implemented in this phase
- An isolated verifier uses PyJWT to verify RS256 signatures.
- Issuer, audience, expiry, issued-at, not-before, subject, and tenant are checked.
- Synthetic RSA keys are used only by tests.
- The verifier is not wired into FastAPI routes.
- No network requests or Microsoft discovery/JWKS requests are performed.

## Critical boundary
The verifier accepts a trusted key resolver supplied by its caller. A future
production integration must implement that resolver using the exact approved
Microsoft Entra OpenID Connect metadata/JWKS endpoint over HTTPS, with safe
key rotation, trusted issuer binding, and explicit tenant/audience configuration.
Never derive a trusted URL or signing key from unvalidated token contents.

## Not implemented
- Production OIDC discovery/JWKS resolver
- Tenant-specific configuration
- Frontend sign-in/token acquisition
- Production role mapping from validated app-role claims
- Validated identity attribution in audit events
- Production route integration or deployment approval

The API must remain fail-closed. These tests do not establish production readiness.
