# Phase 8B.37 — Synthetic Role Mapping

## Scope

This phase implements an offline synthetic test helper only.
It does not authenticate tokens, validate JWT signatures, retrieve
Microsoft Entra claims, or modify production routes.

## Provisional test mapping

- Viewer: cases:read
- Analyst: cases:read, cases:update
- Admin: cases:read, cases:update, users:manage, audit:read

These are provisional synthetic labels, not approved Entra app-role
identifiers or an approved production authorization policy.

## Fail-closed behavior

- Empty roles are rejected.
- Malformed role input is rejected.
- Unknown roles are rejected rather than silently ignored.
- Matching is case-sensitive.
- The returned permission set is immutable.
- Multiple recognized roles combine their permissions.

## Security boundary

The helper does not establish identity or trust. In a future approved
integration, role mapping may only consume claims from a token that
has already passed trusted signature, issuer, audience, tenant and
time validation.

The helper is not imported by the production application and must
not be wired into production routes as an authentication substitute.

## Production blockers

- Approved tenant, issuer and audience configuration
- Trusted Microsoft discovery/JWKS integration
- Approved exact Entra app-role identifiers
- Verified-token-to-principal integration
- Authenticated audit actor attribution
- Frontend sign-in and access-token handling
- Full integration tests and security approval
