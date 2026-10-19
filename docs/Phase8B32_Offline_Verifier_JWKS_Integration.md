# Phase 8B.32 — Offline Verifier/JWKS Integration Tests

## Purpose
Exercise the isolated RS256 token verifier and supplied-JWKS key resolver
together using synthetic RSA keys and synthetic claims.

## Scenarios
- Valid token with matching trusted synthetic key
- Invalid signature and unknown key ID
- Expired token and future not-before claim
- Wrong issuer, audience, and tenant
- Rotation overlap and removal of an old key
- Rejection of private key material in a public JWKS document
- Missing tenant configuration fails closed

## Explicit limitations
- No Microsoft Entra endpoint or discovery document is contacted.
- The supplied JWKS is synthetic and is not authenticated by this test.
- No production API routes or authentication dependencies are changed.
- No frontend sign-in or token storage is implemented.
- No production role mapping or audit identity attribution is implemented.

Production use requires an approved tenant, issuer, audience, trusted HTTPS
discovery/JWKS integration, secure cache/rotation behavior, role mapping,
security review, and deployment approval. The production authentication gate
must remain fail-closed until those steps are complete.
