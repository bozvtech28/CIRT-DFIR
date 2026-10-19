# Phase 8B.29 — Backend Token Verification Plan

## Current status

This is a design and preparation document, not production authentication.
The API authentication gate must remain fail-closed until real verification
is implemented, reviewed, and tested.

## Required implementation controls

1. Use an approved, tenant-specific Microsoft Entra issuer configuration.
2. Obtain signing keys only through trusted Microsoft OpenID Connect metadata
   and JWKS, with HTTPS and safe key-rotation handling.
3. Verify JWT signatures with a vetted library and explicitly permitted
   asymmetric algorithms. Never trust the token header to choose arbitrary
   algorithms or keys.
4. Validate issuer, audience, expiry, not-before, tenant, and required claims.
5. Reject malformed tokens, missing claims, unknown signing keys, invalid
   signatures, wrong audiences, and unauthorized tenants.
6. Map only validated Entra app-role claims to the approved server-side RBAC
   policy. Never accept roles from browser input or request bodies.
7. Keep health-route exposure intentional and protect all sensitive routes.
8. Record the validated principal in audit events; remove hardcoded actor
   identities from production audit attribution.
9. Add isolated tests for valid tokens, invalid signatures, expired tokens,
   wrong issuer/audience/tenant, unknown key IDs, key rotation, missing roles,
   Viewer update denial, and Analyst/Administrator permissions.
10. Keep synthetic JWT/RSA harnesses test-only. Do not wire them into API routes.

## Required administrator configuration

- Approved tenant ID
- Backend API application ID / accepted audience
- Exact trusted issuer
- Approved frontend client ID and API scope
- App-role values and assignments
- Approved redirect URI and internal HTTPS deployment design

## Exit criteria

- Configuration is approved and validated.
- Production token signature verification and claim validation are implemented.
- RBAC uses trusted validated claims.
- Authentication and authorization tests pass.
- Backend regression and frontend production build pass.
- Security review approves deployment.

Until all exit criteria are met, production Entra authentication is NOT
IMPLEMENTED and deployment approval is NOT GRANTED.
