# Phase 8B.34 — Microsoft Entra Configuration Intake

## Purpose
Collect approved, non-secret application configuration before implementing
Microsoft Entra authentication. This phase does not enable authentication.

## Required confirmation from the authorized Entra administrator

- [ ] Tenant ID: the approved Microsoft Entra tenant GUID.
- [ ] API audience: the exact audience expected in API access tokens.
- [ ] Expected issuer: the exact issuer for the selected tenant and token version.
- [ ] Frontend application/client ID.
- [ ] API application registration and exposed scope configuration.
- [ ] Approved app roles and their exact token claim values.
- [ ] Authorized frontend redirect URI(s).
- [ ] Approved logout redirect URI(s).
- [ ] Frontend sign-in flow and API token-acquisition flow.
- [ ] Deployment origin, HTTPS termination, and CORS requirements.
- [ ] API access-token version and expected claims.
- [ ] Approval for logging, audit-subject mapping, and key-rotation behavior.

## Security rules

1. Do not put client secrets, private keys, access tokens, refresh tokens,
   passwords, or certificates' private material in this worksheet.
2. Obtain values through the organization's approved administrative process.
3. Verify the issuer and audience against the approved app registrations.
4. Never accept roles supplied by a browser or request body as proof of identity.
5. Production verification must use trusted Microsoft discovery/JWKS data,
   validated issuer/audience/tenant, and a fixed approved algorithm.
6. Keep the current API authentication gate fail-closed until integration,
   tests, security review, and deployment approval are complete.

## Current status

Offline verifier and JWKS components have synthetic integration tests.
They are not proof of a live Microsoft Entra integration. Production route
wiring, frontend sign-in, trusted role mapping, authenticated audit attribution,
and deployment security controls remain outstanding.
