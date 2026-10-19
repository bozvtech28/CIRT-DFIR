# Phase 8B.9 — Synthetic JWT verification test harness

## Scope
This is an isolated test harness using synthetic HS256 tokens and synthetic keys.
It does not authenticate application users and is not an OIDC implementation.

## Covered behavior
- Valid synthetic token
- Expired token
- Wrong issuer and audience
- Signature tampering
- Unknown key identifier
- Key rotation with old/new key overlap
- Rejection after removal of an old key
- Disallowed algorithm
- Future not-before claim
- Malformed token and missing subject

## Critical limitations
OIDC providers commonly use asymmetric signing keys and provider metadata/JWKS.
This HS256 harness does not test asymmetric signature verification, discovery,
JWKS network behavior, issuer metadata validation, or real provider integration.
It must not be imported by application routes or used in production authentication.

The existing application authentication gate must remain fail-closed.
No provider was contacted, no dependencies were installed, and no server was started.
